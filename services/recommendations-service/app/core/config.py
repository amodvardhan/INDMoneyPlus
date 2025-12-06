"""Configuration settings"""
from pydantic_settings import BaseSettings
from typing import Optional


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
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

