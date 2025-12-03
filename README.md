# Portfolio SuperApp (INDMoney++)

Modular, agentic portfolio management platform with exceptional UX and robust backend.

## Architecture

- **Frontend**: Next.js with Server Components
- **Backend**: Python FastAPI microservices
- **Agent Orchestrator**: LangChain-based agent workflows
- **Database**: PostgreSQL with TimescaleDB for time-series data
- **Cache**: Redis for caching and queues
- **Message Queue**: Kafka for event streaming
- **Vector DB**: Pinecone/Weaviate for agent memory
- **Infrastructure**: Docker & Kubernetes

## Services

### Auth Service (Port 8001)
- User authentication and authorization
- JWT access and refresh tokens
- RBAC support
- Audit logging

### Aggregator Service (Port 8002)
- Multi-custodian holdings aggregation
- CSV/Email/API ingestion
- Instrument normalization
- Reconciliation

### Market Data Service (Port 8003)
- Market prices and timeseries
- OHLC historical data
- Corporate actions
- WebSocket streaming

### Analytics Service (Port 8004)
- Portfolio metrics calculation
- XIRR computation
- Rebalancing simulation

### Agent Orchestrator Service (Port 8005)
- LangChain-powered agent workflows
- Analysis, Rebalance, and Execution-Prep flows
- Vector DB integration
- Source citations

### Order Orchestrator Service (Port 8006)
- Order batching and validation
- Broker routing
- Order lifecycle tracking
- Reconciliation

### Notification Service (Port 8007)
- Multi-channel notifications (Email, SMS, Push)
- Template engine
- Webhook subscriptions
- Background worker with retry logic

## Development

### Prerequisites
- Python 3.11+
- Poetry
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

### Setup

1. **Clone repository**
```bash
git clone <repo-url>
cd INDMoneyPlus
```

2. **Install pre-commit hooks**
```bash
pip install pre-commit
pre-commit install
```

3. **Start services**
```bash
# Start individual service
cd services/auth-service
docker-compose -f docker-compose.dev.yml up

# Or start all services (if orchestrated)
docker-compose up
```

### Coding Standards

See [CODING_STANDARDS.md](.github/CODING_STANDARDS.md) for detailed coding standards.

Key rules:
- Files < 400 LOC, Functions < 80 LOC
- Type annotations mandatory for public functions
- Docstrings for all modules and public functions
- Tests must cover happy path + failure path
- Dependency injection for external services
- Structured logging (no console prints)
- Conventional Commits format

### Testing

```bash
# Run tests for a service
cd services/auth-service
poetry run pytest -v

# Run with coverage
poetry run pytest -v --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy app
```

## Contributing

1. Create a feature branch
2. Follow coding standards
3. Write tests (happy path + failure path)
4. Update CHANGELOG.md
5. Create PR with descriptive title following Conventional Commits
6. Ensure all pre-commit hooks pass

See [COMMIT_CONVENTION.md](.github/COMMIT_CONVENTION.md) for commit message format.

## License

[Your License Here]
