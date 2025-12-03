"""Idempotency support"""
import json
import hashlib
import redis.asyncio as redis
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url)
    return _redis_client


async def check_idempotency(key: str) -> Optional[dict]:
    """
    Check if request with idempotency key was already processed
    
    Args:
        key: Idempotency key
        
    Returns:
        Previous response if exists, None otherwise
    """
    try:
        client = await get_redis_client()
        cached = await client.get(f"idempotency:{key}")
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        logger.error(f"Idempotency check error: {e}")
        return None


async def store_idempotency(key: str, response: dict, ttl: int = 86400):
    """
    Store idempotency key and response
    
    Args:
        key: Idempotency key
        response: Response to cache
        ttl: Time to live in seconds (default 24 hours)
    """
    try:
        client = await get_redis_client()
        await client.setex(
            f"idempotency:{key}",
            ttl,
            json.dumps(response)
        )
    except Exception as e:
        logger.error(f"Idempotency store error: {e}")


def generate_idempotency_key(data: dict) -> str:
    """Generate idempotency key from data"""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()

