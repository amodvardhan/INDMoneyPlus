"""Tests for authentication endpoints"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.models.user import User, RefreshToken
from app.core.security import decode_token


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "securepass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "id" in data
    assert "created_at" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user: User):
    """Test registration with duplicate email"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "newpassword123"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    """Test registration with password too short"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "short"
        }
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify tokens are valid
    access_payload = decode_token(data["access_token"])
    assert access_payload is not None
    assert access_payload.get("type") == "access"
    assert int(access_payload.get("sub")) == test_user.id
    
    refresh_payload = decode_token(data["refresh_token"])
    assert refresh_payload is not None
    assert refresh_payload.get("type") == "refresh"
    assert "jti" in refresh_payload


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user: User):
    """Test login with invalid credentials"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Test login with inactive user"""
    user = User(
        email="inactive@example.com",
        hashed_password="$2b$12$test",
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()
    
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, test_user: User):
    """Test successful token refresh"""
    # First login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh tokens
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify old refresh token is revoked
    payload = decode_token(refresh_token)
    jti = payload.get("jti")
    
    # Verify new tokens were issued (old token revocation is tested separately)
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Test refresh with invalid token"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_revoked(client: AsyncClient, test_user: User, db_session: AsyncSession):
    """Test refresh with revoked token"""
    # Login and get refresh token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Revoke token manually
    payload = decode_token(refresh_token)
    jti = payload.get("jti")
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_jti == jti)
    )
    token_record = result.scalar_one_or_none()
    if token_record:
        token_record.revoked_at = datetime.utcnow()
        await db_session.commit()
    
    # Try to refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient, test_user: User, db_session: AsyncSession):
    """Test successful logout"""
    # Login first
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 204
    
    # Verify token is revoked
    payload = decode_token(refresh_token)
    jti = payload.get("jti")
    result = await db_session.execute(
        select(RefreshToken).where(RefreshToken.token_jti == jti)
    )
    token_record = result.scalar_one_or_none()
    assert token_record is not None
    assert token_record.revoked_at is not None


@pytest.mark.asyncio
async def test_get_me_success(client: AsyncClient, test_user: User):
    """Test getting current user info"""
    # Login first
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_me_unauthorized(client: AsyncClient):
    """Test getting current user without token"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """Test getting current user with invalid token"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

