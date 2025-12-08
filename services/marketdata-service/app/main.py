"""
Market Data Service - Market data ingestion, caching, and timeseries storage
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.core.config import settings
from app.core.database import engine
from app.core.cache import close_redis
from app.models.instrument import Base
from app.core.adapters import InMemoryAdapter
from app.api import prices, instruments, corporate_actions, websocket, market_health

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
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown: Close Redis connections
    await close_redis()


app = FastAPI(
    title="Market Data Service",
    description="Market data ingestion, caching, and timeseries storage",
    version=settings.service_version,
    lifespan=lifespan
)

# Include routers
app.include_router(prices.router, prefix="/api/v1", tags=["prices"])
app.include_router(instruments.router, prefix="/api/v1/instruments", tags=["instruments"])
app.include_router(corporate_actions.router, prefix="/api/v1/corporate-actions", tags=["corporate-actions"])
app.include_router(market_health.router, prefix="/api/v1", tags=["market-health"])
app.include_router(websocket.router, tags=["websocket"])


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
    uvicorn.run(app, host="0.0.0.0", port=8003)
