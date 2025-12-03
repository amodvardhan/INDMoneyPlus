# API Gateway

Lightweight edge API gateway with authentication and request routing.

## Features

- JWT token verification via auth service
- Request proxying to backend microservices
- CORS handling
- Health check endpoint

## Running Locally

```bash
poetry install
poetry run uvicorn app.main:app --reload --port 8000
```

## Environment Variables

- `AUTH_SERVICE_URL`: URL of auth service (default: http://localhost:8001)
- `AGGREGATOR_SERVICE_URL`: URL of aggregator service
- `MARKETDATA_SERVICE_URL`: URL of market data service
- `ANALYTICS_SERVICE_URL`: URL of analytics service
- `AGENT_ORCHESTRATOR_URL`: URL of agent orchestrator
- `ORDER_ORCHESTRATOR_URL`: URL of order orchestrator
- `NOTIFICATION_SERVICE_URL`: URL of notification service
- `ADMIN_SERVICE_URL`: URL of admin service

