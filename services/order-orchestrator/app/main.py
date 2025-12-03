"""
Order Orchestrator Service - Order batching, validation, and routing
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from app.core.config import settings
from app.core.database import engine
from app.models.order import Base
from app.core.events import close_kafka_producer
from app.api import orders, reconcile

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

orders_placed_total = Counter(
    "orders_placed_total",
    "Total orders placed",
    ["broker", "status"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown: Close Kafka producer
    await close_kafka_producer()


app = FastAPI(
    title="Order Orchestrator",
    description="Order batching, validation, routing, and lifecycle tracking",
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
app.include_router(orders.router, prefix="/api/v1", tags=["orders"])
app.include_router(reconcile.router, prefix="/api/v1", tags=["reconcile"])


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
    uvicorn.run(app, host="0.0.0.0", port=8006)
