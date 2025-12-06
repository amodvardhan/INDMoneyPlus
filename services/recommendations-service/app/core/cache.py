"""Redis caching utilities for recommendations"""
import json
import redis.asyncio as redis
from typing import Optional, Dict, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client"""
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
                decode_responses=True
            )
            # Test connection
            await _redis_client.ping()
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Caching disabled.")
            _redis_client = None
            return None
    
    return _redis_client


async def get_cached_recommendations(
    cache_key: str,
    limit: int,
    recommendation_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get cached recommendations from Redis
    
    Args:
        cache_key: Cache key (e.g., "recommendations:top:10")
        limit: Number of recommendations requested
        recommendation_type: Optional filter type
        
    Returns:
        Cached recommendations dict or None if not found
    """
    try:
        client = await get_redis_client()
        if not client:
            return None
        
        # Build full cache key
        full_key = f"recommendations:{cache_key}"
        if recommendation_type:
            full_key += f":{recommendation_type}"
        full_key += f":{limit}"
        
        cached = await client.get(full_key)
        if cached:
            data = json.loads(cached)
            logger.debug(f"Cache hit for key: {full_key}")
            return data
        else:
            logger.debug(f"Cache miss for key: {full_key}")
            return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def set_cached_recommendations(
    cache_key: str,
    data: Dict[str, Any],
    ttl_seconds: int,
    limit: int,
    recommendation_type: Optional[str] = None
):
    """
    Cache recommendations in Redis
    
    Args:
        cache_key: Cache key (e.g., "recommendations:top")
        data: Recommendations data to cache
        ttl_seconds: Time to live in seconds
        limit: Number of recommendations
        recommendation_type: Optional filter type
    """
    try:
        client = await get_redis_client()
        if not client:
            return
        
        # Build full cache key
        full_key = f"recommendations:{cache_key}"
        if recommendation_type:
            full_key += f":{recommendation_type}"
        full_key += f":{limit}"
        
        await client.setex(
            full_key,
            ttl_seconds,
            json.dumps(data, default=str)  # Handle datetime serialization
        )
        logger.debug(f"Cached recommendations with key: {full_key}, TTL: {ttl_seconds}s")
    except Exception as e:
        logger.error(f"Cache set error: {e}")


async def invalidate_recommendations_cache(pattern: str = "recommendations:*"):
    """
    Invalidate all recommendation caches matching pattern
    
    Args:
        pattern: Redis key pattern (default: "recommendations:*")
    """
    try:
        client = await get_redis_client()
        if not client:
            return
        
        # Find all keys matching pattern
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching pattern: {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis cache connection closed")

