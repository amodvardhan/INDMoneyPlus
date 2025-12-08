"""Configuration settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    service_name: str = "recommendations-service"
    service_version: str = "1.0.0"
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_db"
    
    # Redis
    redis_url: str = "redis://redis:6379/3"  # Use DB 3 for recommendations cache
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: Optional[int] = None  # If None, uses recommendation_refresh_hours * 3600
    
    # External services
    marketdata_service_url: str = "http://localhost:8003"
    aggregator_service_url: str = "http://localhost:8004"
    agent_orchestrator_url: str = "http://agent-orchestrator:8084"
    
    # Recommendation settings
    max_recommendations: int = 20
    recommendation_validity_days: int = 7
    recommendation_refresh_hours: int = 1  # Regenerate if older than this
    
    model_config = SettingsConfigDict(
        # Load from multiple env files in order (later files override earlier ones)
        env_file=[
            ".env",
            ".env.local",
            ".env.dev.local"
        ],
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True
    )


# Load settings and log configuration
settings = Settings()

# Log which env files exist (for debugging)
env_files = [".env", ".env.local", ".env.dev.local"]
found_files = [f for f in env_files if os.path.exists(f)]
if found_files:
    logger.info(f"Loaded environment files: {', '.join(found_files)}")
else:
    logger.warning("No .env files found. Using defaults and environment variables only.")

# Log market data service URL for debugging
logger.info(f"Market data service URL: {settings.marketdata_service_url}")

