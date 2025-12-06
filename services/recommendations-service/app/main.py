"""
Recommendations Service - Stock recommendations based on research, news, and expert analysis
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
from app.core.config import settings
from app.core.database import engine
from app.models import Base
from app.api import recommendations

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
    
    # Initialize Redis cache connection
    from app.core.cache import get_redis_client
    await get_redis_client()
    
    yield
    
    # Shutdown: Close Redis connection
    from app.core.cache import close_redis
    await close_redis()


app = FastAPI(
    title="Recommendations Service",
    description="Stock recommendations based on research, news, and expert analysis",
    version=settings.service_version,
    lifespan=lifespan
)

# Include routers
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])


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
    uvicorn.run(app, host="0.0.0.0", port=8088)

