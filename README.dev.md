# Developer Guide - Portfolio SuperApp

This guide helps you set up and work with the Portfolio SuperApp development environment.

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd INDMoneyPlus

# 2. Bootstrap environment (creates .env.dev.local automatically if needed)
./scripts/bootstrap-dev.sh

# 3. Start all services
make dev-up

# 4. Verify services are healthy
make health-check
```

**Note**: The bootstrap script will automatically create `.env.dev.local` from `.env.example` if it doesn't exist. You can manually copy and customize it if needed:

```bash
cp .env.example .env.dev.local
# Edit .env.dev.local with your values
```

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Make** (for convenience commands)
- **VS Code** (recommended for debugging)
- **curl** (for health checks and testing)

## Environment Setup

### 1. Environment Variables

Create your development environment file:

```bash
# Option 1: Copy from example (if .env.example exists)
cp .env.example .env.dev.local

# Option 2: Let bootstrap script create it automatically
# (The bootstrap script will create .env.dev.local with defaults if .env.example doesn't exist)
```

The `.env.dev.local` file is git-ignored and contains your local development settings.

Key variables to review:
- `POSTGRES_USER` / `POSTGRES_PASSWORD` - Database credentials
- `JWT_SECRET` - JWT signing secret (use a strong value in production)
- `LOG_LEVEL` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)

**Important**: External API keys (`OPENAI_API_KEY`, `PINECONE_API_KEY`, `ALPHAVANTAGE_API_KEY`, etc.) are **NOT required** for development or PoC demos. The system uses mocks/in-memory alternatives by default:
- **Agent Orchestrator**: Works without OpenAI (uses structured/rule-based execution)
- **Vector DB**: Uses in-memory storage (no Pinecone needed)
- **Market Data**: Uses mock data (no external API needed)

Only set these keys if you want to use real external services instead of mocks.

### 2. Start Development Environment

```bash
# Start all services with hot-reload
make dev-up

# Or manually:
docker compose -f docker-compose.dev.yml up --build
```

This starts:
- **Infrastructure**: Postgres, Redis, Redpanda (Kafka), Vector DB (Chroma)
- **Backend Services**: All Python FastAPI services with hot-reload
- **Frontend**: Next.js with hot-reload
- **Observability**: Prometheus and Grafana

### 3. Service URLs

Once started, services are available at:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js web app |
| API Gateway | http://localhost:8000 | Main API entry point |
| Auth Service | http://localhost:8080 | Authentication |
| Marketdata | http://localhost:8081 | Market data |
| Analytics | http://localhost:8082 | Portfolio analytics |
| Aggregator | http://localhost:8083 | Holdings aggregation |
| Agent Orchestrator | http://localhost:8084 | AI agent workflows |
| Notification | http://localhost:8085 | Notifications |
| Order Orchestrator | http://localhost:8086 | Order management |
| Admin Service | http://localhost:8087 | Admin operations |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3001 | Dashboards (admin/admin) |

## Database Setup

### Run Migrations

```bash
# Run all migrations
make migrate

# Or manually for a specific service
cd services/auth-service
poetry run alembic upgrade head
```

### Seed Test Data

```bash
# Seed all test data
make seed

# Or manually
./scripts/bootstrap-dev.sh --seed-only
```

### Access Database

```bash
# Connect to Postgres
docker compose -f docker-compose.dev.yml exec postgres psql -U user -d portfolio_superapp

# List databases
docker compose -f docker-compose.dev.yml exec postgres psql -U user -c "\l"
```

## Development Workflow

### Hot Reload

All services support hot-reload:
- **Python services**: Code changes trigger uvicorn auto-reload
- **Next.js**: Fast Refresh enabled for React components

### Running a Single Service

To run only specific services for faster iteration:

1. Create `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  # Only run auth-service and dependencies
  auth-service:
    profiles: []
```

2. Start with override:
```bash
docker compose -f docker-compose.dev.yml -f docker-compose.override.yml up
```

### Viewing Logs

```bash
# All services
make dev-logs

# Specific service
docker compose -f docker-compose.dev.yml logs -f auth-service

# Last 100 lines
docker compose -f docker-compose.dev.yml logs --tail=100 auth-service
```

### Stopping Services

```bash
# Stop all services
make dev-down

# Stop and remove volumes (clean slate)
docker compose -f docker-compose.dev.yml down -v
```

## Debugging

### VS Code Debugging

#### Backend (Python) Debugging

1. Ensure services are running: `make dev-up`
2. Open VS Code
3. Go to Run and Debug (Cmd+Shift+D / Ctrl+Shift+D)
4. Select a service configuration (e.g., "Python: Attach to auth-service")
5. Set breakpoints in your code
6. Start debugging (F5)

**Note**: Services must be running with debugpy installed (handled automatically in dev mode).

#### Frontend (Next.js) Debugging

1. Select "Next.js: Debug Server" configuration
2. Set breakpoints in your TypeScript/React code
3. Start debugging (F5)
4. Open http://localhost:3000 in Chrome

### Manual Debugging

#### Python Services

To debug a Python service manually:

```bash
# Attach debugpy to running container
docker compose -f docker-compose.dev.yml exec auth-service \
  poetry run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

#### Frontend

Next.js debugging is enabled by default. Use Chrome DevTools:
1. Open Chrome
2. Navigate to chrome://inspect
3. Click "Open dedicated DevTools for Node"

## Testing

### Run All Tests

```bash
make test
```

This runs:
- Unit tests for all Python services
- Integration tests against dockerized infrastructure
- Frontend tests (if configured)

### Run Tests for Specific Service

```bash
cd services/auth-service
poetry install
poetry run pytest -v

# With coverage
poetry run pytest -v --cov=app --cov-report=html
```

### Test Against CI Environment

```bash
# Simulate CI build and test
make ci-run

# Or manually
./scripts/ci_local.sh
```

## Linting and Code Quality

### Run Linters

```bash
make lint
```

### Format Code

```bash
# Python services
cd services/auth-service
poetry run black .
poetry run ruff check --fix .

# Frontend
cd web
pnpm format  # if configured
```

## Common Tasks

### Check Service Health

```bash
make health-check

# Or manually
curl http://localhost:8080/health
curl http://localhost:8081/health
# ... etc
```

### Rebuild a Service

```bash
# Rebuild specific service
docker compose -f docker-compose.dev.yml build auth-service

# Rebuild and restart
docker compose -f docker-compose.dev.yml up -d --build auth-service
```

### Reset Database

```bash
# Stop services and remove volumes
docker compose -f docker-compose.dev.yml down -v

# Restart and bootstrap
make dev-up
./scripts/bootstrap-dev.sh
```

### View Service Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:8080/metrics

# Or view in Grafana
open http://localhost:3001
# Login: admin/admin
```

## Mock External Services

External services (broker APIs, market data providers) are mocked in development:

- **Vector DB**: Chroma container (in-memory or persistent)
- **Kafka**: Redpanda (Kafka-compatible)
- **Market Data**: In-memory adapter (configurable via `ADAPTER_TYPE`)

To use real services, set environment variables in `.env.dev.local`:
```bash
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
ALPHAVANTAGE_API_KEY=...
```

## Troubleshooting

### Services Won't Start

1. Check if ports are already in use:
```bash
lsof -i :8080
lsof -i :3000
```

2. Check Docker logs:
```bash
docker compose -f docker-compose.dev.yml logs
```

3. Verify Docker has enough resources (4GB RAM, 2 CPUs recommended)

### Database Connection Issues

1. Ensure Postgres is healthy:
```bash
docker compose -f docker-compose.dev.yml ps postgres
```

2. Check database exists:
```bash
docker compose -f docker-compose.dev.yml exec postgres psql -U user -c "\l"
```

3. Verify connection string in service logs

### Hot Reload Not Working

1. Check volume mounts:
```bash
docker compose -f docker-compose.dev.yml config | grep volumes
```

2. Verify file permissions (services run as root in dev mode)

3. Check uvicorn reload logs:
```bash
docker compose -f docker-compose.dev.yml logs auth-service | grep reload
```

### Debug Port Already in Use

If debug port (e.g., 5678) is already in use:
1. Change port in `.env.dev.local`:
```bash
AUTH_SERVICE_DEBUG_PORT=5679
```

2. Update VS Code launch.json accordingly

## CI/CD

### Local CI Simulation

```bash
make ci-run
```

This:
1. Builds production Docker images
2. Runs linters
3. Runs tests
4. Validates builds

### GitHub Actions

CI runs on push/PR to `main` or `develop`:
- Lint checks
- Unit and integration tests
- Docker image builds
- Coverage reports

See `.github/workflows/dev-ci.yml` for details.

## Example API Calls

### Health Check

```bash
curl http://localhost:8080/health
```

### Register User

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### Login

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Get Holdings (with auth token)

```bash
TOKEN="your-jwt-token-here"
curl http://localhost:8083/api/v1/holdings \
  -H "Authorization: Bearer $TOKEN"
```

## Next Steps

1. **Read Architecture Docs**: See `docs/ARCHITECTURE.md`
2. **Review Service READMEs**: Each service has its own README
3. **Explore API Docs**: OpenAPI docs at http://localhost:8000/docs
4. **Set Up Pre-commit Hooks**: `pre-commit install`

## Getting Help

- Check service logs: `make dev-logs`
- Review health status: `make health-check`
- Check VS Code tasks: Cmd+Shift+P → "Tasks: Run Task"
- Review this guide and main README.md

## Acceptance Criteria

✅ `docker compose -f docker-compose.dev.yml up --build` starts all services  
✅ All `/health` endpoints return 200  
✅ `./scripts/bootstrap-dev.sh` runs migrations and seeds data  
✅ `make test` runs all tests successfully  
✅ VS Code debugger can attach to backend services  
✅ Hot-reload works for code changes  
✅ `make ci-run` simulates CI build/test locally  

