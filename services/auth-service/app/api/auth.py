"""Authentication endpoints"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.rate_limit import check_rate_limit, reset_rate_limit
from app.core.audit import log_audit_event
from app.core.dependencies import get_current_user
from app.models.user import User, RefreshToken
from app.schemas.user import (
    RegisterRequest,
    LoginRequest,
    UserRead,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.core.config import settings

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    if request.client:
        return request.client.host
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("user-agent", "unknown")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Log audit event
    await log_audit_event(
        db=db,
        user_id=new_user.id,
        action="register",
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={"email": user_data.email}
    )
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Login and get access + refresh tokens"""
    # Rate limiting
    rate_limit_key = f"login_attempts:{login_data.email}"
    is_allowed, remaining = await check_rate_limit(
        key=rate_limit_key,
        max_attempts=settings.rate_limit_login_attempts,
        window_seconds=settings.rate_limit_window_seconds
    )
    
    if not is_allowed:
        await log_audit_event(
            db=db,
            user_id=None,
            action="login_rate_limit_exceeded",
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={"email": login_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again later."
        )
    
    # Verify user
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        await log_audit_event(
            db=db,
            user_id=user.id if user else None,
            action="login_failed",
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={"email": login_data.email, "reason": "invalid_credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        await log_audit_event(
            db=db,
            user_id=user.id,
            action="login_failed",
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={"email": login_data.email, "reason": "account_inactive"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Reset rate limit on successful login
    await reset_rate_limit(rate_limit_key)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token, jti = create_refresh_token(data={"sub": str(user.id)})
    
    # Store refresh token in database
    expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_token_expiration)
    refresh_token_record = RefreshToken(
        user_id=user.id,
        token_jti=jti,
        expires_at=expires_at
    )
    db.add(refresh_token_record)
    await db.commit()
    
    # Log successful login
    await log_audit_event(
        db=db,
        user_id=user.id,
        action="login_success",
        ip=get_client_ip(request),
        user_agent=get_user_agent(request),
        metadata={"email": login_data.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_data: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    # Decode refresh token
    payload = decode_token(refresh_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    jti = payload.get("jti")
    user_id = int(payload.get("sub"))
    
    if not jti or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if refresh token exists and is not revoked
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_jti == jti,
            RefreshToken.user_id == user_id
        )
    )
    refresh_token_record = result.scalar_one_or_none()
    
    if not refresh_token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )
    
    if refresh_token_record.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    if refresh_token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token, new_jti = create_refresh_token(data={"sub": str(user.id)})
    
    # Revoke old refresh token and store new one
    refresh_token_record.revoked_at = datetime.utcnow()
    
    expires_at = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_token_expiration)
    new_refresh_token_record = RefreshToken(
        user_id=user.id,
        token_jti=new_jti,
        expires_at=expires_at
    )
    db.add(new_refresh_token_record)
    await db.commit()
    
    # Log refresh
    await log_audit_event(
        db=db,
        user_id=user.id,
        action="token_refresh",
        ip=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    logout_data: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Logout and revoke refresh token"""
    # Decode refresh token
    payload = decode_token(logout_data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    jti = payload.get("jti")
    user_id = int(payload.get("sub")) if payload.get("sub") else None
    
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Revoke refresh token
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_jti == jti)
    )
    refresh_token_record = result.scalar_one_or_none()
    
    if refresh_token_record and not refresh_token_record.revoked_at:
        refresh_token_record.revoked_at = datetime.utcnow()
        await db.commit()
    
    # Log logout
    await log_audit_event(
        db=db,
        user_id=user_id,
        action="logout",
        ip=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return None


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user

