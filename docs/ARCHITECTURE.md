# Architecture Documentation

## Overview

Portfolio Superapp is a microservices-based platform for comprehensive portfolio management with AI-powered agent orchestration.

## System Architecture

```
┌─────────────┐
│   Next.js   │
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ API Gateway │
└──────┬──────┘
       │
       ├──► Auth Service
       ├──► Aggregator Service
       ├──► Market Data Service
       ├──► Analytics Service
       ├──► Agent Orchestrator
       ├──► Order Orchestrator
       ├──► Notification Service
       └──► Admin Service
```

## Services

### API Gateway
- Lightweight edge API
- JWT token verification
- Request routing to backend services
- CORS handling

### Auth Service
- User registration and authentication
- JWT token generation
- OIDC connector support

### Aggregator Service
- Broker/CAS data aggregation
- File and email ingestion
- Data normalization

### Market Data Service
- Real-time and historical market data
- Redis caching
- Timeseries data storage

### Analytics Service
- Portfolio calculations
- XIRR computation
- Risk metrics (Sharpe ratio, volatility)

### Agent Orchestrator
- LangChain agent integration
- Tool adapters for market data and analytics
- Vector store (Pinecone) integration
- Portfolio analysis and rebalance proposals

### Order Orchestrator
- Order batching
- Idempotency handling
- Broker API connectors

### Notification Service
- Email notifications
- SMS notifications
- Push notifications
- Webhook delivery

### Admin Service
- Account reconciliations
- Operations dashboards
- Audit logging

### Worker Service
- Background job processing (Celery/Temporal)
- Rebalance tasks
- Tax harvesting
- Heavy compute jobs

## Data Flow

1. User authenticates via Auth Service
2. Frontend receives JWT token
3. API Gateway verifies token and routes requests
4. Services process requests and interact with databases
5. Worker service handles background tasks
6. Notifications sent via Notification Service

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Next.js 14 (App Router, TypeScript)
- **Database**: PostgreSQL
- **Cache**: Redis
- **Vector DB**: Pinecone
- **Worker**: Celery/Temporal
- **Infrastructure**: Kubernetes, Terraform
- **CI/CD**: GitHub Actions

## Security

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting at API Gateway
- Circuit breakers for external APIs
- Secrets management via Vault/cloud secrets manager

## Observability

- OpenTelemetry for distributed tracing
- Structured logging (JSON)
- Metrics collection
- Health check endpoints

