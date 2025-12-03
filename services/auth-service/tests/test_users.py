"""Tests for user management endpoints"""
import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_list_users_as_superuser(client: AsyncClient, test_superuser: User):
    """Test listing users as superuser"""
    # Login as superuser
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_superuser.email,
            "password": "adminpassword123"
        }
    )
    access_token = login_response.json()["access_token"]
    
    # List users
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_users_as_regular_user(client: AsyncClient, test_user: User):
    """Test listing users as regular user (should fail)"""
    # Login as regular user
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Try to list users
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403
    assert "permissions" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_users_unauthorized(client: AsyncClient):
    """Test listing users without authentication"""
    response = await client.get("/api/v1/users")
    assert response.status_code == 401

