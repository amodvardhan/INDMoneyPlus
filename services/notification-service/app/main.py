"""
Notification Service - Centralized notification hub
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from app.core.config import settings
from app.core.database import engine
from app.models.notification import Base
from app.core.workers.notification_worker import NotificationWorker
from app.api import notifications, webhooks, events

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

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total notifications sent",
    ["channel", "status"]
)

# Global worker instance
worker: NotificationWorker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global worker
    
    # Startup: Create database tables
    async with engine.begin() as conn:
        # Don't create tables here - use Alembic migrations instead
        # await conn.run_sync(Base.metadata.create_all)
    
    # Start background worker if enabled
    if settings.worker_enabled:
        worker = NotificationWorker()
        await worker.start()
    
    yield
    
    # Shutdown: Stop worker
    if worker:
        await worker.stop()


app = FastAPI(
    title="Notification Service",
    description="Centralized notification hub for email, SMS, push, and webhooks",
    version=settings.service_version,
    lifespan=lifespan
)

# Middleware for Prometheus metrics
@app.middleware("http")
async def add_prometheus_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    endpoint = request.url.path
    method = request.method
    status_code = response.status_code

    http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(process_time)
    
    return response

# Include routers
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "version": settings.service_version,
        "worker_enabled": settings.worker_enabled
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
