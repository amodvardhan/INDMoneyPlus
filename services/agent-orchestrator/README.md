# Agent Orchestrator Service

LangChain-powered orchestrator that composes tools (marketdata, analytics, aggregator, order-orchestrator) to perform multi-step workflows: portfolio analysis, rebalance proposal generation, trade-envelope creation (but NOT execution), and generate explainable rationale. Fully auditable and safe with human-in-the-loop for execution.

## Features

- **Three Agent Flows**: Analysis, Rebalance, Execution-Prep
- **Tool Adapters**: HTTP clients for internal services
- **Source Citations**: All outputs include source citations
- **Vector DB Integration**: Agent memory with Pinecone/Weaviate/in-memory support
- **Audit Logging**: Complete action logs for every agent run
- **Human-in-the-Loop**: Execution requires explicit approval
- **LangChain Integration**: Function-calling style for deterministic outputs

## Database Models

- **AgentRun**: `id`, `user_id`, `flow_type`, `input_json`, `output_json`, `status`, `executed_by`, `executed_at`, `created_at`
- **AgentActionLog**: `id`, `agent_run_id`, `step`, `tool_called`, `tool_input`, `tool_output`, `timestamp`

## API Endpoints

### Agent Flows

- `POST /api/v1/agents/analyze` - Execute portfolio analysis flow
  - Request: `{"portfolio_id": int, "user_id": int}`
  - Response: `AnalysisResponse` with explanation, metrics, and sources

- `POST /api/v1/agents/rebalance` - Generate rebalance proposal
  - Request: `{"portfolio_id": int, "user_id": int, "target_alloc": dict}`
  - Response: `RebalanceResponse` with trade proposals and costs

- `POST /api/v1/agents/prepare_execution` - Prepare order envelopes (requires human confirmation)
  - Request: `{"agent_run_id": int, "user_id": int, "human_confirmation": true}`
  - Response: `ExecutionPrepResponse` with order envelopes

### Audit & Logs

- `GET /api/v1/agents/{id}/logs` - Get action logs for an agent run
- `GET /api/v1/agents/{id}` - Get agent run details

### Health & Metrics

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

## Running Locally

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 15+
- OpenAI API key (optional, for LLM features)

### Setup

1. **Install dependencies:**
```bash
poetry install
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run database migrations:**
```bash
poetry run alembic upgrade head
```

4. **Start the service:**
```bash
poetry run uvicorn app.main:app --reload --port 8005
```

### Using Docker Compose

```bash
cd services/agent-orchestrator
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- PostgreSQL on port 5432
- Agent Orchestrator service on port 8005

## Agent Flows

### 1. Analysis Flow

Fetches portfolio holdings, computes metrics, and produces a written explanation with structured JSON metrics.

**Example:**
```bash
curl -X POST "http://localhost:8005/api/v1/agents/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "user_id": 1
  }'
```

**Response includes:**
- Human-readable explanation
- Structured metrics with source citations
- All sources used in analysis

### 2. Rebalance Flow

Fetches current holdings, runs rebalancer simulation, and produces trade proposals with estimated costs/tax.

**Example:**
```bash
curl -X POST "http://localhost:8005/api/v1/agents/rebalance" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "user_id": 1,
    "target_alloc": {
      "EQUITY": 0.6,
      "BOND": 0.4
    }
  }'
```

**Response includes:**
- List of proposed trades with quantities and prices
- Total estimated cost and tax
- Explanation of rebalance rationale
- Source citations

### 3. Execution-Prep Flow

Takes an approved rebalance proposal and produces signed order envelopes ready for order-orchestrator. **Requires human confirmation.**

**Example:**
```bash
curl -X POST "http://localhost:8005/api/v1/agents/prepare_execution" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_run_id": 123,
    "user_id": 1,
    "human_confirmation": true
  }'
```

**Response includes:**
- Order envelopes in format consumable by order-orchestrator
- Summary explanation
- Status: `pending_approval` (requires final approval before execution)

## Source Citations

All agent outputs include source citations indicating:
- Which service produced each data point
- Which endpoint was called
- Timestamp of data retrieval
- Specific data point referenced

Example citation:
```json
{
  "service": "marketdata-service",
  "endpoint": "/api/v1/price/RELIANCE/latest",
  "timestamp": "2024-01-01T00:00:00",
  "data_point": "price"
}
```

## Vector DB Integration

The service uses vector DB for agent memory:
- **Pinecone**: Production-ready vector store
- **Weaviate**: Alternative vector store
- **In-Memory**: For development/testing (default)

Vector store stores:
- Portfolio analysis context
- Rebalance proposal context
- Execution preparation context

## Testing

### Run All Tests

```bash
poetry run pytest -v
```

### Run Tests with Coverage

```bash
poetry run pytest -v --cov=app --cov-report=html
```

### Test Categories

- **test_agents.py**: Agent endpoint tests with mocked services

## Manual Verification Steps

### 1. Analysis Flow

```bash
# Start services (aggregator, marketdata, analytics)
# Then run analysis
curl -X POST "http://localhost:8005/api/v1/agents/analyze" \
  -H "Content-Type: application/json" \
  -d '{"portfolio_id": 1, "user_id": 1}'
```

**Expected**: `200 OK` with analysis response containing:
- Explanation
- Metrics array with source citations
- Sources array

### 2. Rebalance Flow

```bash
curl -X POST "http://localhost:8005/api/v1/agents/rebalance" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "user_id": 1,
    "target_alloc": {"EQUITY": 0.6, "BOND": 0.4}
  }'
```

**Expected**: `200 OK` with rebalance response containing:
- Proposal array with trades
- Total estimated cost
- Explanation

### 3. Execution-Prep Flow

```bash
# First, get agent_run_id from rebalance flow
# Then prepare execution
curl -X POST "http://localhost:8005/api/v1/agents/prepare_execution" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_run_id": 123,
    "user_id": 1,
    "human_confirmation": true
  }'
```

**Expected**: `200 OK` with execution prep response containing:
- Order envelopes array
- Explanation
- Status: `pending_approval`

### 4. Get Agent Logs

```bash
curl "http://localhost:8005/api/v1/agents/123/logs"
```

**Expected**: `200 OK` with array of action logs showing:
- Each tool call
- Input/output for each step
- Timestamps

### 5. Verify Human Confirmation Required

```bash
curl -X POST "http://localhost:8005/api/v1/agents/prepare_execution" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_run_id": 123,
    "user_id": 1,
    "human_confirmation": false
  }'
```

**Expected**: `400 Bad Request` with error message about human confirmation

## Sample Trade Envelope JSON

```json
{
  "agent_run_id": 456,
  "order_envelopes": [
    {
      "instrument_id": 1,
      "ticker": "TCS",
      "exchange": "NSE",
      "action": "BUY",
      "quantity": 50,
      "order_type": "MARKET",
      "metadata": {
        "estimated_price": 3500.00,
        "estimated_cost": 175000.00,
        "source_agent_run_id": 123
      },
      "source_agent_run_id": 123
    }
  ],
  "explanation": "Execution Preparation Summary:...",
  "requires_approval": true,
  "status": "pending_approval"
}
```

## Acceptance Criteria

✅ **Database Models**
- [x] AgentRun model with all required fields
- [x] AgentActionLog model for audit trail
- [x] Proper indexes for performance

✅ **Tool Adapters**
- [x] MarketDataTool for market data service
- [x] AnalyticsTool for analytics service
- [x] AggregatorTool for aggregator service
- [x] OrderTool for order orchestrator
- [x] Source citation generation for all tool calls

✅ **Agent Flows**
- [x] Analysis Flow: fetch holdings → compute metrics → generate explanation
- [x] Rebalance Flow: fetch holdings → simulate rebalance → generate proposals
- [x] Execution-Prep Flow: validate proposal → create order envelopes
- [x] Human confirmation required for execution prep

✅ **Source Citations**
- [x] All outputs include source citations
- [x] Citations include service, endpoint, timestamp, data point

✅ **Vector DB**
- [x] Vector store integration (Pinecone/Weaviate/in-memory)
- [x] Context storage for agent memory
- [x] Search functionality

✅ **Audit Logging**
- [x] Action logs for every tool call
- [x] Step-by-step audit trail
- [x] GET endpoint for retrieving logs

✅ **Observability**
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Proper logging

✅ **Testing**
- [x] Unit tests for agent endpoints
- [x] Integration tests with mocked services
- [x] Tests for all three flows

✅ **DevOps**
- [x] Dockerfile for containerization
- [x] docker-compose.dev.yml with Postgres
- [x] .env.example
- [x] Alembic migrations
- [x] CI/CD workflow

## Development

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy app
```

### Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## License

[Your License Here]
