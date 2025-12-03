"""
Aggregator Service - Broker/CAS data aggregation and file/email ingestion
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.core.config import settings
from app.core.database import engine
from app.models.aggregator import Base
from app.core.idempotency import close_redis
from app.api import ingest, holdings

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
    
    yield
    
    # Shutdown: Close Redis connections
    await close_redis()


app = FastAPI(
    title="Aggregator Service",
    description="Broker/CAS data aggregation and file/email ingestion",
    version=settings.service_version,
    lifespan=lifespan
)

# Include routers
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(holdings.router, prefix="/api/v1/holdings", tags=["holdings"])


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
    uvicorn.run(app, host="0.0.0.0", port=8002)
