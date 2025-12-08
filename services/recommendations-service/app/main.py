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
from app.api import recommendations, news, dashboard_notifications

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
    import httpx
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Redis cache connection
    from app.core.cache import get_redis_client
    await get_redis_client()
    
    # CRITICAL: Test market data service connectivity on startup
    logger.info("🔍 Testing market data service connectivity...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_url = f"{settings.marketdata_service_url}/health"
            response = await client.get(health_url)
            if response.status_code == 200:
                logger.info(f"✅ Market data service is accessible at {settings.marketdata_service_url}")
            else:
                logger.warning(
                    f"⚠️  Market data service returned status {response.status_code} at {settings.marketdata_service_url}"
                )
    except httpx.ConnectError as e:
        logger.error(
            f"❌ CRITICAL: Cannot connect to market data service at {settings.marketdata_service_url}. "
            f"Error: {e}. Fresh prices will not be available until this is fixed!"
        )
    except Exception as e:
        logger.warning(f"⚠️  Market data service health check failed: {e}")
    
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
app.include_router(news.router, prefix="/api/v1", tags=["news"])
app.include_router(dashboard_notifications.router, prefix="/api/v1", tags=["notifications"])


@app.get("/health")
async def health():
    """Health check endpoint with dependency status"""
    import httpx
    
    health_status = {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "dependencies": {}
    }
    
    # Check market data service
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.marketdata_service_url}/health")
            health_status["dependencies"]["market_data_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "url": settings.marketdata_service_url,
                "status_code": response.status_code
            }
    except Exception as e:
        health_status["dependencies"]["market_data_service"] = {
            "status": "unreachable",
            "url": settings.marketdata_service_url,
            "error": str(e)
        }
        health_status["status"] = "degraded"  # Service works but dependency is down
    
    return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)

