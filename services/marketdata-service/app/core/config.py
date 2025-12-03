"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/marketdata_db"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Adapter Configuration
    adapter_type: str = "in_memory"  # in_memory, alphavantage, tiingo
    
    # AlphaVantage API (if using)
    alphavantage_api_key: Optional[str] = None
    
    # Tiingo API (if using)
    tiingo_api_key: Optional[str] = None
    
    # Auth Service URL (for token verification)
    auth_service_url: str = "http://localhost:8001"
    
    # Service Info
    service_name: str = "marketdata-service"
    service_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

