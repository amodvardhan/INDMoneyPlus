"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/notification_db"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_queue_key: str = "notification_queue"
    
    # Transport Configuration
    email_transport_type: str = "in_memory"  # in_memory, sendgrid
    sms_transport_type: str = "in_memory"  # in_memory, twilio
    push_transport_type: str = "in_memory"  # in_memory, firebase
    
    # SendGrid (if using)
    sendgrid_api_key: Optional[str] = None
    sendgrid_from_email: Optional[str] = None
    
    # Twilio (if using)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None
    
    # Firebase (if using)
    firebase_credentials_path: Optional[str] = None
    
    # Worker Configuration
    worker_enabled: bool = True
    worker_batch_size: int = 10
    worker_poll_interval: float = 1.0
    max_retry_attempts: int = 3
    retry_backoff_base: float = 2.0  # Exponential backoff base
    
    # Service Info
    service_name: str = "notification-service"
    service_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

