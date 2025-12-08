"""Application configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/marketdata_db"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Adapter Configuration
    adapter_type: str = "auto"  # auto (prefer Tiingo if key available, else Yahoo), yahoo_finance, tiingo, in_memory (synthetic), alphavantage
    
    # AlphaVantage API (if using)
    alphavantage_api_key: Optional[str] = None
    
    # Tiingo API (if using)
    tiingo_api_key: Optional[str] = None
    
    # Auth Service URL (for token verification)
    auth_service_url: str = "http://localhost:8001"
    
    # Service Info
    service_name: str = "marketdata-service"
    service_version: str = "0.1.0"
    
    model_config = SettingsConfigDict(
        # Load from multiple env files in order (later files override earlier ones)
        # .env.dev.local has highest priority, then .env.local, then .env
        env_file=[
            ".env",
            ".env.local",
            ".env.dev.local"
        ],
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Also check for files that might not exist (ignore if missing)
        env_ignore_empty=True
    )


settings = Settings()

# Log which env files exist (for debugging)
env_files = [".env", ".env.local", ".env.dev.local"]
found_files = [f for f in env_files if os.path.exists(f)]
if found_files:
    logger.info(f"Loaded environment files: {', '.join(found_files)}")
else:
    logger.warning("No .env files found. Using defaults and environment variables only.")

# Log adapter configuration (without exposing API keys)
if settings.tiingo_api_key:
    logger.info(f"Tiingo API key found. Adapter type: {settings.adapter_type}")
else:
    logger.info(f"No Tiingo API key found. Adapter type: {settings.adapter_type}")

