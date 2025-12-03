"""Security utilities"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def generate_jti() -> str:
    """Generate a unique JWT ID (JTI) for refresh tokens"""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.jwt_access_token_expiration)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
    """Create a JWT refresh token and return (token, jti)"""
    to_encode = data.copy()
    jti = generate_jti()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=settings.jwt_refresh_token_expiration)
    
    to_encode.update({
        "exp": expire,
        "jti": jti,
        "type": "refresh"
    })
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt, jti


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from access token"""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    return None

