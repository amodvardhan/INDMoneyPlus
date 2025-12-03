"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/order_orchestrator_db"
    
    # Redis Configuration (for idempotency)
    redis_url: str = "redis://localhost:6379/0"
    
    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_orders: str = "order-events"
    kafka_enabled: bool = True
    
    # Order Validation
    min_lot_size: int = 1
    max_order_value: float = 10000000.0  # 10M
    margin_check_enabled: bool = True
    
    # Service Info
    service_name: str = "order-orchestrator"
    service_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

