# Order Orchestrator Service

Responsible for batching, idempotency, order envelope validation, and routing to broker connectors. Supports order lifecycle tracking (placed, acked, filled, settled) and reconciliation endpoints.

## Features

- **Order Batching**: Group multiple orders into batches
- **Idempotency**: Support for idempotency keys to prevent duplicate orders
- **Order Validation**: Margin checks, lot size validation, price limits
- **Broker Routing**: Route orders to appropriate broker connectors
- **Order Lifecycle**: Track orders through placed → acked → filled → settled
- **Reconciliation**: Generate reconciliation reports with P&L calculations
- **Event Publishing**: Publish order events to Kafka
- **Mock Connectors**: Zerodha-mock and Alpaca-mock connectors for testing

## Database Models

- **Order**: `id`, `portfolio_id`, `broker`, `instrument_id`, `qty`, `price_limit`, `side`, `status`, `created_at`, `executed_at`, `ext_order_id`, `fill_price`, `fill_qty`, `batch_id`
- **OrderBatch**: `id`, `user_id`, `portfolio_id`, `orders_json`, `status`, `created_at`, `idempotency_key`
- **BrokerConnectorConfig**: `id`, `broker_name`, `config_json`, `active`, `created_at`, `updated_at`

## API Endpoints

### Orders

- `POST /api/v1/orders` - Create order batch
  - Request: `{"portfolio_id": int, "orders": [...], "idempotency_key": "..."}`
  - Headers: `Idempotency-Key: <key>` (optional)
  - Response: `OrderBatchResponse` with batch_id and proposed routing

- `GET /api/v1/orders/{id}` - Get order status
  - Response: `OrderRead` with order details

- `POST /api/v1/orders/{id}/simulate_fill` - Simulate order fill (for testing)
  - Request: `{"fills": [{"order_id": int, "fill_price": float, "fill_qty": float}]}`
  - Response: Fill confirmation

### Reconciliation

- `GET /api/v1/reconcile/{batch_id}` - Get reconciliation report
  - Response: `ReconciliationReport` with P&L and order statistics

### Health & Metrics

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

## Running Locally

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 15+
- Redis 7+
- Kafka (optional, for event publishing)

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
poetry run uvicorn app.main:app --reload --port 8006
```

### Using Docker Compose

```bash
cd services/order-orchestrator
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Kafka + Zookeeper on port 9092
- Order Orchestrator service on port 8006

## Order Validation

Orders are validated before processing:
- **Lot Size**: Minimum quantity validation
- **Price Limits**: Price must be positive and within limits
- **Margin Check**: Mock margin validation (configurable)
- **Side Validation**: Must be BUY or SELL

## Idempotency

Idempotency keys prevent duplicate order processing:
- Use `Idempotency-Key` header or include in request body
- Same key returns cached response
- Keys are stored in Redis with 24-hour TTL

## Broker Connectors

### Zerodha Mock Connector

- Generates deterministic order IDs
- Supports simulated fills for testing
- Returns order status: placed, acked, filled

### Alpaca Mock Connector

- Similar to Zerodha connector
- Generates Alpaca-style order IDs
- Supports simulated fills

## Order Lifecycle

1. **placed**: Order created and sent to broker
2. **acked**: Broker acknowledged order
3. **filled**: Order executed with fill price/qty
4. **settled**: Order settlement completed
5. **cancelled**: Order cancelled
6. **rejected**: Order rejected by broker

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

- **test_orders.py**: Order endpoint tests
- **test_reconcile.py**: Reconciliation tests

## Manual Verification Steps

### 1. Create Order Batch

```bash
curl -X POST "http://localhost:8006/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{
    "portfolio_id": 1,
    "orders": [
      {
        "instrument_id": 1,
        "qty": 100,
        "side": "BUY",
        "price_limit": 2500.0
      },
      {
        "instrument_id": 2,
        "qty": 50,
        "side": "SELL",
        "price_limit": 2600.0
      }
    ]
  }'
```

**Expected**: `200 OK` with batch_id and proposed routing

### 2. Get Order Status

```bash
# Get order_id from step 1
curl "http://localhost:8006/api/v1/orders/{order_id}"
```

**Expected**: `200 OK` with order details and status

### 3. Simulate Fill

```bash
curl -X POST "http://localhost:8006/api/v1/orders/{order_id}/simulate_fill" \
  -H "Content-Type: application/json" \
  -d '{
    "fills": [
      {
        "order_id": 1,
        "fill_price": 2500.0,
        "fill_qty": 100
      }
    ]
  }'
```

**Expected**: `200 OK` with fill confirmation

### 4. Reconcile Batch

```bash
# Get batch_id from step 1
curl "http://localhost:8006/api/v1/reconcile/{batch_id}"
```

**Expected**: `200 OK` with reconciliation report containing:
- Total orders, filled orders, pending orders
- Total qty, filled qty
- Total value, filled value
- Expected P&L, Actual P&L

### 5. Verify Idempotency

```bash
# Send same request with same idempotency key
curl -X POST "http://localhost:8006/api/v1/orders" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-123" \
  -d '{
    "portfolio_id": 1,
    "orders": [...]
  }'
```

**Expected**: `200 OK` with same batch_id (cached response)

### 6. Health Check

```bash
curl http://localhost:8006/health
```

**Expected**: `200 OK` with service status

### 7. Metrics

```bash
curl http://localhost:8006/metrics
```

**Expected**: `200 OK` with Prometheus metrics format

## Acceptance Criteria

✅ **Database Models**
- [x] Order model with all required fields
- [x] OrderBatch model with idempotency support
- [x] BrokerConnectorConfig model

✅ **Order Validation**
- [x] Lot size validation
- [x] Price limit validation
- [x] Margin check (mock)
- [x] Side validation

✅ **Idempotency**
- [x] Idempotency key support via header
- [x] Redis-based idempotency storage
- [x] Cached response for duplicate requests

✅ **Broker Connectors**
- [x] Zerodha-mock connector
- [x] Alpaca-mock connector
- [x] Simulated fill support
- [x] Deterministic behavior

✅ **Order Lifecycle**
- [x] Status tracking (placed, acked, filled, settled)
- [x] Fill price/qty tracking
- [x] Event publishing on status changes

✅ **Reconciliation**
- [x] Reconciliation report endpoint
- [x] P&L calculation (expected vs actual)
- [x] Order statistics

✅ **Event Publishing**
- [x] Kafka event publishing
- [x] Order status change events
- [x] Graceful fallback if Kafka unavailable

✅ **Observability**
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Proper logging

✅ **Testing**
- [x] Unit tests for orders
- [x] Integration tests for reconciliation
- [x] Idempotency tests

✅ **DevOps**
- [x] Dockerfile for containerization
- [x] docker-compose.dev.yml with Postgres + Redis + Kafka
- [x] .env.example
- [x] Alembic migrations
- [x] CI/CD workflow

## Sample Reconciliation Report

```json
{
  "batch_id": 123,
  "total_orders": 2,
  "filled_orders": 2,
  "pending_orders": 0,
  "cancelled_orders": 0,
  "total_qty": 150.0,
  "filled_qty": 150.0,
  "total_value": 380000.0,
  "filled_value": 380000.0,
  "expected_pnl": 5000.0,
  "actual_pnl": 5000.0,
  "orders": [...]
}
```

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

