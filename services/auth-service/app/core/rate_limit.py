"""Rate limiting utilities using Redis"""
import redis.asyncio as redis
from typing import Optional, Tuple
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


async def check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int]:
    """
    Check if rate limit is exceeded.
    Returns (is_allowed, remaining_attempts)
    """
    try:
        client = await get_redis_client()
        current = await client.get(key)
        
        if current is None:
            # First attempt, set counter
            await client.setex(key, window_seconds, 1)
            return True, max_attempts - 1
        
        current_count = int(current)
        if current_count >= max_attempts:
            # Rate limit exceeded
            ttl = await client.ttl(key)
            return False, 0
        
        # Increment counter
        await client.incr(key)
        return True, max_attempts - (current_count + 1)
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # Fail open - allow request if Redis is down
        return True, max_attempts


async def reset_rate_limit(key: str) -> None:
    """Reset rate limit counter (e.g., on successful login)"""
    try:
        client = await get_redis_client()
        await client.delete(key)
    except Exception as e:
        logger.error(f"Rate limit reset failed: {e}")


async def close_redis() -> None:
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None

