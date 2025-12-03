"""
Agent Orchestrator - LangChain agents and tool adapters
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.core.config import settings
from app.core.database import engine
from app.models.agent import Base
from app.core.vector_store import get_vector_store
from app.api import agents

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup: Don't create tables here - use Alembic migrations instead
    # Tables are created via Alembic migrations in bootstrap-dev.sh
    
    # Initialize vector store (optional - can work without it)
    try:
        await get_vector_store()
    except Exception as e:
        # Log but don't fail if vector store is unavailable
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Vector store initialization failed: {e}. Continuing without vector store.")
    
    yield


app = FastAPI(
    title="Agent Orchestrator",
    description="LangChain agents, tool adapters, and vector store integration",
    version=settings.service_version,
    lifespan=lifespan
)

# Include routers
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
