"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/agent_orchestrator_db"
    
    # Vector DB Configuration
    vector_db_type: str = "pinecone"  # pinecone, weaviate, or in_memory
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None  # DEPRECATED: Not needed with Pinecone v3+ SDK
    pinecone_index_name: str = "agent-memory"
    weaviate_url: Optional[str] = None
    
    # LLM Configuration
    llm_provider: str = "openai"  # openai, anthropic, etc.
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    temperature: float = 0.0  # Deterministic outputs
    
    # Service URLs
    marketdata_service_url: str = "http://localhost:8003"
    analytics_service_url: str = "http://localhost:8004"
    aggregator_service_url: str = "http://localhost:8002"
    order_orchestrator_url: str = "http://localhost:8006"
    auth_service_url: str = "http://localhost:8001"
    
    # Service Info
    service_name: str = "agent-orchestrator"
    service_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

