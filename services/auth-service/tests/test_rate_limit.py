"""Tests for rate limiting"""
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_rate_limit_login_attempts(client: AsyncClient, test_user: User):
    """Test rate limiting on login attempts"""
    # Make multiple failed login attempts
    for i in range(6):  # Exceed the limit of 5
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        if i < 5:
            assert response.status_code == 401
        else:
            # 6th attempt should be rate limited
            assert response.status_code == 429
            assert "too many" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rate_limit_reset_on_success(client: AsyncClient, test_user: User):
    """Test that rate limit resets on successful login"""
    # Make some failed attempts
    for _ in range(3):
        await client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
    
    # Successful login should reset the counter
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    
    # Should be able to make more attempts after successful login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401  # Not rate limited

