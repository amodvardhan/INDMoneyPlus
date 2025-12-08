"""Redis caching utilities for market data prices"""
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client with connection pooling"""
    global _redis_client
    
    if _redis_client is None:
        try:
            redis_url = getattr(settings, 'redis_url', None)
            if not redis_url:
                logger.warning("Redis URL not configured, caching disabled")
                return None
            
            _redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            await _redis_client.ping()
            logger.info("✅ Redis cache connected for market data")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            _redis_client = None
            return None
    
    return _redis_client


def _get_price_cache_key(ticker: str, exchange: str) -> str:
    """Generate cache key for price"""
    return f"price:latest:{ticker.upper()}:{exchange.upper()}"


async def get_cached_price(ticker: str, exchange: str) -> Optional[Dict[str, Any]]:
    """
    Get cached latest price from Redis
    
    Args:
        ticker: Stock ticker symbol
        exchange: Exchange code (NSE, NASDAQ, etc.)
        
    Returns:
        Cached price data dict or None if not found/expired or stale
    """
    try:
        client = await get_redis_client()
        if not client:
            return None
        
        cache_key = _get_price_cache_key(ticker, exchange)
        cached = await client.get(cache_key)
        
        if cached:
            data = json.loads(cached)
            
            # Validate that cached price is from today
            timestamp_str = data.get("timestamp")
            if timestamp_str:
                try:
                    from datetime import datetime
                    if isinstance(timestamp_str, str):
                        cached_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    else:
                        cached_timestamp = timestamp_str
                    
                    # Check if cached price is from today
                    now = datetime.utcnow()
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    # If cached price is not from today, it's stale
                    if cached_timestamp < today_start:
                        logger.debug(
                            f"❌ Cached price for {ticker} on {exchange} is from {cached_timestamp.date()}, "
                            f"not today. Invalidating cache."
                        )
                        await client.delete(cache_key)
                        return None
                    
                    # Also check if cache is too old (more than 2 minutes for real-time prices)
                    age_seconds = (now - cached_timestamp).total_seconds()
                    if age_seconds > 120:  # 2 minutes - very short TTL for real-time prices
                        logger.debug(
                            f"❌ Cached price for {ticker} on {exchange} is {age_seconds:.0f}s old (>2min). Invalidating cache."
                        )
                        await client.delete(cache_key)
                        return None
                except Exception as e:
                    logger.warning(f"Error validating cache timestamp for {ticker}: {e}")
                    # If we can't validate, don't use cached data
                    return None
            
            logger.debug(f"✅ Cache HIT for {ticker} on {exchange}")
            return data
        else:
            logger.debug(f"❌ Cache MISS for {ticker} on {exchange}")
            return None
    except Exception as e:
        logger.error(f"Cache get error for {ticker} on {exchange}: {e}")
        return None


async def set_cached_price(
    ticker: str,
    exchange: str,
    price_data: Dict[str, Any],
    ttl_seconds: int = 300  # Default 5 minutes for latest prices
):
    """
    Cache latest price in Redis with TTL
    
    Args:
        ticker: Stock ticker symbol
        exchange: Exchange code
        price_data: Price data dict to cache
        ttl_seconds: Time to live in seconds (default: 60s for latest prices)
    """
    try:
        client = await get_redis_client()
        if not client:
            return
        
        cache_key = _get_price_cache_key(ticker, exchange)
        
        # Add cache metadata
        price_data["_cached_at"] = datetime.utcnow().isoformat()
        price_data["_cache_ttl"] = ttl_seconds
        
        await client.setex(
            cache_key,
            ttl_seconds,
            json.dumps(price_data, default=str)
        )
        logger.debug(f"💾 Cached price for {ticker} on {exchange}, TTL: {ttl_seconds}s")
    except Exception as e:
        logger.error(f"Cache set error for {ticker} on {exchange}: {e}")


async def invalidate_price_cache(ticker: Optional[str] = None, exchange: Optional[str] = None):
    """
    Invalidate price cache for specific ticker/exchange or all prices
    
    Args:
        ticker: Optional ticker to invalidate (if None, invalidates all)
        exchange: Optional exchange to invalidate (if None, invalidates all)
    """
    try:
        client = await get_redis_client()
        if not client:
            return
        
        if ticker and exchange:
            # Invalidate specific ticker
            cache_key = _get_price_cache_key(ticker, exchange)
            deleted = await client.delete(cache_key)
            if deleted:
                logger.info(f"🗑️  Invalidated cache for {ticker} on {exchange}")
        else:
            # Invalidate all price caches
            pattern = "price:latest:*"
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await client.delete(*keys)
                logger.info(f"🗑️  Invalidated {deleted} price cache keys")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")


async def flush_all_price_cache():
    """
    Flush all price-related cache from Redis
    
    This is a destructive operation - use with caution!
    """
    try:
        client = await get_redis_client()
        if not client:
            logger.warning("Redis not available, cannot flush cache")
            return False
        
        # Find all price cache keys
        pattern = "price:*"
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            deleted = await client.delete(*keys)
            logger.info(f"🗑️  Flushed {deleted} price cache keys from Redis")
            return True
        else:
            logger.info("No price cache keys found to flush")
            return True
    except Exception as e:
        logger.error(f"Error flushing price cache: {e}")
        return False


async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        client = await get_redis_client()
        if not client:
            return {"status": "disabled", "keys": 0}
        
        # Count price cache keys
        pattern = "price:*"
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        return {
            "status": "active",
            "total_keys": len(keys),
            "redis_url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else "configured"
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"status": "error", "error": str(e)}


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis cache connection closed")
