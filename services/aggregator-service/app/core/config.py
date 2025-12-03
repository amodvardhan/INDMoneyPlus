"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/aggregator_db"
    
    # Redis Configuration (for idempotency)
    redis_url: str = "redis://localhost:6379/0"
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_holdings: str = "holdings-updates"
    kafka_topic_reconciliation: str = "reconciliation-events"
    
    # Market Data Service URL (for instrument lookup)
    marketdata_service_url: str = "http://localhost:8003"
    
    # Auth Service URL (for token verification)
    auth_service_url: str = "http://localhost:8001"
    
    # Service Info
    service_name: str = "aggregator-service"
    service_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

