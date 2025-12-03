"""Idempotency utilities using Redis"""
import redis.asyncio as redis
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    return _redis_client


async def check_idempotency(key: str) -> bool:
    """
    Check if a statement has already been processed.
    
    Args:
        key: Statement hash key
        
    Returns:
        True if already processed, False otherwise
    """
    try:
        client = await get_redis_client()
        exists = await client.exists(key)
        return exists > 0
    except Exception as e:
        logger.error(f"Idempotency check failed: {e}")
        # Fail open - allow processing if Redis is down
        return False


async def mark_as_processed(key: str, ttl_seconds: int = 86400 * 30) -> None:
    """
    Mark a statement as processed.
    
    Args:
        key: Statement hash key
        ttl_seconds: Time to live in seconds (default: 30 days)
    """
    try:
        client = await get_redis_client()
        await client.setex(key, ttl_seconds, "processed")
    except Exception as e:
        logger.error(f"Failed to mark statement as processed: {e}")


async def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

