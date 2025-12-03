"""Authentication utilities for verifying tokens from auth service"""
import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token with auth service.
    Returns user info if valid, None otherwise.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

