"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/auth_db"
    
    # JWT Configuration
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expiration: int = 3600  # 1 hour
    jwt_refresh_token_expiration: int = 604800  # 7 days
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Rate Limiting
    rate_limit_login_attempts: int = 5  # Max attempts
    rate_limit_window_seconds: int = 300  # 5 minutes
    
    # Security
    password_min_length: int = 8
    
    # Service Info
    service_name: str = "auth-service"
    service_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

