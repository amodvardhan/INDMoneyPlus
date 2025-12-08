"""
API Gateway - Lightweight edge API with authentication
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
from typing import Optional
from jose import jwt, JWTError

app = FastAPI(
    title="Portfolio Superapp API Gateway",
    description="Edge API gateway with authentication and routing",
    version="0.1.0",
    redirect_slashes=False  # Disable automatic trailing slash redirects to prevent 307 errors
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs (in production, use service discovery)
SERVICE_URLS = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8080"),
    "aggregator": os.getenv("AGGREGATOR_SERVICE_URL", "http://aggregator-service:8083"),
    "marketdata": os.getenv("MARKETDATA_SERVICE_URL", "http://marketdata-service:8081"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics-service:8082"),
    "agent": os.getenv("AGENT_ORCHESTRATOR_URL", "http://agent-orchestrator:8084"),
    "agents": os.getenv("AGENT_ORCHESTRATOR_URL", "http://agent-orchestrator:8084"),  # Alias for plural form
    "order": os.getenv("ORDER_ORCHESTRATOR_URL", "http://order-orchestrator:8086"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8085"),
    "admin": os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8087"),
    "recommendations": os.getenv("RECOMMENDATIONS_SERVICE_URL", "http://recommendations-service:8088"),
}

async def verify_token(request: Request) -> Optional[str]:
    """Verify JWT token from Authorization header"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    
    # Decode token locally (JWT is stateless, no need to call auth service)
    try:
        from jose import jwt, JWTError
        import os
        
        # Get JWT secret from environment or use default for dev
        jwt_secret = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        if payload.get("type") == "access":
            return payload.get("sub")  # user_id
    except (JWTError, Exception):
            pass
    
    return None

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

# Auth endpoints (public, no authentication required) - MUST be before general proxy routes
@app.post("/api/v1/auth/{path:path}")
async def proxy_auth_post(path: str, request: Request):
    """Proxy auth POST requests (no token required)"""
    if "auth" not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail="Service not found")
    
    url = f"{SERVICE_URLS['auth']}/api/v1/auth/{path}"
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=body, timeout=30.0)
            try:
                response_data = response.json()
            except Exception:
                # Handle non-JSON responses (like 500 errors)
                response_data = {"detail": response.text or f"Error: {response.status_code}"}
            return JSONResponse(
                content=response_data,
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")

@app.get("/api/v1/auth/{path:path}")
async def proxy_auth_get(path: str, request: Request):
    """Proxy auth GET requests - forward Authorization header for protected endpoints"""
    if "auth" not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail="Service not found")
    
    url = f"{SERVICE_URLS['auth']}/api/v1/auth/{path}"
    params = dict(request.query_params)
    
    # Forward Authorization header if present (needed for /me endpoint)
    headers = {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            try:
                response_data = response.json()
            except Exception:
                response_data = {"detail": response.text or f"Error: {response.status_code}"}
            return JSONResponse(
                content=response_data,
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")

# Handle notifications endpoint without path (base endpoint)
@app.get("/api/v1/notifications")
async def proxy_notifications_base(request: Request):
    """Proxy GET requests to notifications base endpoint"""
    user_id = await verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    url = f"{SERVICE_URLS['recommendations']}/api/v1/notifications"
    params = dict(request.query_params)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params=params,
                headers={"X-User-ID": user_id},
                timeout=30.0
            )
            try:
                content = response.json()
            except Exception:
                content = {"detail": response.text or f"Error: {response.status_code}"}
            return JSONResponse(
                content=content,
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")

@app.get("/api/v1/{service}/{path:path}")
async def proxy_get(service: str, path: str, request: Request):
    """Proxy GET requests to backend services"""
    if service not in SERVICE_URLS and service not in ["news", "notifications"]:
        raise HTTPException(status_code=404, detail="Service not found")
    
    user_id = await verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # For agent-orchestrator, the path already includes "agents" prefix
    # For recommendations, the path includes "recommendations" prefix
    # For news and notifications, they're part of recommendations service but at root /api/v1
    # So we need to include the service name in the path
    if service in ["agent", "agents"]:
        url = f"{SERVICE_URLS[service]}/api/v1/agents/{path}"
    elif service == "recommendations":
        url = f"{SERVICE_URLS[service]}/api/v1/recommendations/{path}"
    elif service == "news":
        # News is part of recommendations service
        # Path should be the ticker (e.g., "HDFCBANK" from /api/v1/news/HDFCBANK)
        if path and path.strip() and path != "/":
            clean_path = path.lstrip('/')
            # Construct URL: http://recommendations-service:8088/api/v1/news/{ticker}
            url = f"{SERVICE_URLS['recommendations']}/api/v1/news/{clean_path}"
        else:
            # Base news endpoint (shouldn't normally be called)
            url = f"{SERVICE_URLS['recommendations']}/api/v1/news"
    elif service == "notifications":
        # Dashboard notifications are part of recommendations service
        # This handles paths like "notifications/unread-count"
        clean_path = path.lstrip('/') if path else ""
        if clean_path:
            url = f"{SERVICE_URLS['recommendations']}/api/v1/notifications/{clean_path}"
        else:
            # Should not reach here due to base route above, but handle just in case
            url = f"{SERVICE_URLS['recommendations']}/api/v1/notifications"
    else:
        url = f"{SERVICE_URLS[service]}/api/v1/{path}"
    
    params = dict(request.query_params)
    
    # Log the request for debugging (especially for news)
    if service == "news":
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📰 Proxying news request: {url} with params {params}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                params=params,
                headers={"X-User-ID": user_id},
                timeout=30.0
            )
            try:
                content = response.json()
            except Exception:
                # Handle non-JSON responses (like 500 errors with HTML/text)
                content = {"detail": response.text or f"Error: {response.status_code}"}
            return JSONResponse(
                content=content,
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            # Better error message for debugging
            error_msg = f"Service unavailable: {str(e)}"
            if service == "news":
                error_msg += f" (URL: {url})"
            raise HTTPException(status_code=502, detail=error_msg)

@app.post("/api/v1/{service}/{path:path}")
async def proxy_post(service: str, path: str, request: Request):
    """Proxy POST requests to backend services"""
    if service not in SERVICE_URLS and service not in ["news", "notifications"]:
        raise HTTPException(status_code=404, detail="Service not found")
    
    user_id = await verify_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # For agent-orchestrator, the path already includes "agents" prefix
    # For recommendations, the path includes "recommendations" prefix
    # For news and notifications, they're part of recommendations service but at root /api/v1
    # So we need to include the service name in the path
    if service in ["agent", "agents"]:
        url = f"{SERVICE_URLS[service]}/api/v1/agents/{path}"
    elif service == "recommendations":
        url = f"{SERVICE_URLS[service]}/api/v1/recommendations/{path}"
    elif service == "news":
        # News is part of recommendations service
        url = f"{SERVICE_URLS['recommendations']}/api/v1/news/{path}"
    elif service == "notifications":
        # Dashboard notifications are part of recommendations service
        # This handles paths like "notifications/unread-count"
        clean_path = path.lstrip('/') if path else ""
        if clean_path:
            url = f"{SERVICE_URLS['recommendations']}/api/v1/notifications/{clean_path}"
        else:
            # Should not reach here due to base route above, but handle just in case
            url = f"{SERVICE_URLS['recommendations']}/api/v1/notifications"
    else:
        url = f"{SERVICE_URLS[service]}/api/v1/{path}"
    
    body = await request.json()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=body,
                headers={"X-User-ID": user_id},
                timeout=30.0
            )
            try:
                content = response.json()
            except Exception:
                # Handle non-JSON responses (like 500 errors with HTML/text)
                content = {"detail": response.text or f"Error: {response.status_code}"}
            return JSONResponse(
                content=content,
                status_code=response.status_code
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

