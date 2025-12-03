# Market Data Service

Production-ready market data service for ingesting and serving market prices, timeseries data, and corporate actions. Supports real-time-like APIs with synthetic data generation, OHLC historical endpoints, and a pluggable adapter interface for integrating real market data providers.

## Features

- **Price Data**: Real-time-like latest prices and historical OHLC timeseries
- **Instruments Management**: CRUD operations for market instruments
- **Corporate Actions**: Ingestion and querying of corporate actions (dividends, splits, etc.)
- **WebSocket Streaming**: Real-time price updates via WebSocket
- **Pluggable Adapters**: Interface for integrating AlphaVantage, Tiingo, or other providers
- **TimescaleDB Support**: Optimized timeseries storage with fallback to Postgres
- **Observability**: Prometheus metrics and health checks

## Database Models

- **Instrument**: `id`, `isin`, `ticker`, `exchange`, `name`, `asset_class`, `timezone`, `created_at`
- **PricePoint**: `id`, `instrument_id`, `timestamp`, `open`, `high`, `low`, `close`, `volume`
- **CorporateAction**: `id`, `instrument_id`, `type`, `effective_date`, `payload_json`, `created_at`

## API Endpoints

### Prices

- `GET /api/v1/prices/{ticker}?exchange=...&from=...&to=...` - Get historical price timeseries
- `GET /api/v1/price/{ticker}/latest?exchange=...` - Get latest price quote

### Instruments

- `GET /api/v1/instruments` - List instruments (with optional search, exchange, asset_class filters)
- `GET /api/v1/instruments/{ticker}?exchange=...` - Get instrument by ticker and exchange
- `POST /api/v1/instruments` - Create new instrument

### Corporate Actions

- `POST /api/v1/corporate-actions` - Create corporate action (requires authentication)
- `GET /api/v1/corporate-actions?instrument_id=...` - List corporate actions

### WebSocket

- `WS /ws/prices` - Stream real-time price updates

### Health & Metrics

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

## Running Locally

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 15+ (or TimescaleDB)
- Redis 7+

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

4. **Seed initial instruments:**
```bash
poetry run python scripts/seed_instruments.py
```

5. **Start the service:**
```bash
poetry run uvicorn app.main:app --reload --port 8003
```

### Using Docker Compose

```bash
cd services/marketdata-service
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- TimescaleDB (or Postgres) on port 5432
- Redis on port 6379
- Market Data service on port 8003

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string (asyncpg driver)
- `REDIS_URL`: Redis connection string
- `ADAPTER_TYPE`: Market data adapter type (in_memory, alphavantage, tiingo)
- `AUTH_SERVICE_URL`: URL of auth service for token verification

## Seeding Instruments

The service includes a script to seed initial instruments:

```bash
poetry run python scripts/seed_instruments.py
```

This will create instruments for:
- Indian stocks: RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK (NSE)
- US stocks: AAPL, GOOGL, MSFT, AMZN, TSLA (NASDAQ)

## WebSocket Streaming

The WebSocket endpoint streams price updates directly from the market data adapter. Prices are fetched on-demand when clients subscribe to tickers.

### Using WebSocket

1. **Connect to WebSocket:**
```bash
# Connect to WebSocket
wscat -c ws://localhost:8003/ws/prices

# Subscribe to a ticker
{"type": "subscribe", "ticker": "RELIANCE", "exchange": "NSE"}

# You'll receive price updates in real-time
```

2. **Unsubscribe:**
```bash
{"type": "unsubscribe", "ticker": "RELIANCE", "exchange": "NSE"}
```

The WebSocket fetches prices directly from the configured adapter (InMemoryAdapter, AlphaVantage, Tiingo, etc.) and streams them to subscribed clients.

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

- **test_instruments.py**: Instrument CRUD operations
- **test_prices.py**: Price endpoints (latest, timeseries)
- **test_adapter.py**: Market data adapter interface

## Manual Verification Steps

### 1. Seed Instruments

```bash
poetry run python scripts/seed_instruments.py
```

**Expected**: Instruments created in database

### 2. Get Latest Price

```bash
curl "http://localhost:8003/api/v1/price/RELIANCE/latest?exchange=NSE"
```

**Expected**: `200 OK` with latest price data

### 3. Get Price Timeseries

```bash
curl "http://localhost:8003/api/v1/prices/RELIANCE?exchange=NSE&from=2024-01-01T00:00:00&to=2024-01-07T23:59:59"
```

**Expected**: `200 OK` with array of price points

### 4. List Instruments

```bash
curl "http://localhost:8003/api/v1/instruments"
```

**Expected**: `200 OK` with list of instruments

### 5. Search Instruments

```bash
curl "http://localhost:8003/api/v1/instruments?search=Reliance"
```

**Expected**: `200 OK` with filtered instruments

### 6. Create Corporate Action (requires auth)

```bash
# First, get a token from auth service
TOKEN="your_access_token_here"

curl -X POST "http://localhost:8003/api/v1/corporate-actions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instrument_id": 1,
    "type": "DIVIDEND",
    "effective_date": "2024-03-15T00:00:00",
    "payload_json": {"amount": 10.5, "currency": "INR"}
  }'
```

**Expected**: `201 Created` with corporate action data

### 7. WebSocket Streaming

```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:8003/ws/prices

# Subscribe
{"type": "subscribe", "ticker": "RELIANCE", "exchange": "NSE"}

# You should receive price updates
```

**Expected**: Real-time price updates in JSON format

### 8. Health Check

```bash
curl http://localhost:8003/health
```

**Expected**: `200 OK` with service status

### 9. Metrics

```bash
curl http://localhost:8003/metrics
```

**Expected**: `200 OK` with Prometheus metrics format

## Acceptance Criteria

✅ **Database Models**
- [x] Instrument model with all required fields
- [x] PricePoint model with OHLC data
- [x] CorporateAction model with flexible JSON payload
- [x] Proper indexes and foreign key constraints

✅ **Migrations**
- [x] Alembic migrations for all tables
- [x] TimescaleDB hypertable support (with Postgres fallback)
- [x] Proper indexes for timeseries queries

✅ **Price Endpoints**
- [x] GET /api/v1/prices/{ticker} returns timeseries data
- [x] GET /api/v1/price/{ticker}/latest returns latest price
- [x] Proper error handling for non-existent instruments
- [x] Date range filtering

✅ **Instrument Endpoints**
- [x] GET /api/v1/instruments lists all instruments
- [x] GET /api/v1/instruments/{ticker} gets specific instrument
- [x] POST /api/v1/instruments creates new instrument
- [x] Search and filtering support

✅ **Corporate Actions**
- [x] POST /api/v1/corporate-actions requires authentication
- [x] GET /api/v1/corporate-actions lists actions
- [x] Proper validation and error handling

✅ **WebSocket**
- [x] WebSocket endpoint for streaming prices
- [x] Subscribe/unsubscribe functionality
- [x] Real-time price updates from adapter

✅ **Adapter Interface**
- [x] Abstract base class for adapters
- [x] InMemoryAdapter implementation
- [x] Structure ready for AlphaVantage/Tiingo adapters

✅ **Observability**
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Proper logging

✅ **Testing**
- [x] Unit tests for endpoints
- [x] Integration tests with test database
- [x] Adapter tests

✅ **DevOps**
- [x] Dockerfile for containerization
- [x] docker-compose.dev.yml with TimescaleDB/Postgres + Redis
- [x] Seed data script
- [x] .env.example

## Adapter Interface

The service uses a pluggable adapter pattern for market data providers:

```python
from app.core.adapters.base import MarketDataAdapter

class MyAdapter(MarketDataAdapter):
    async def get_latest_price(self, ticker: str, exchange: str):
        # Implement latest price fetching
        pass
    
    async def get_historical_prices(self, ticker: str, exchange: str, from_date, to_date):
        # Implement historical data fetching
        pass
    
    async def search_instruments(self, query: str):
        # Implement instrument search
        pass
```

To use a custom adapter, update the `get_adapter()` function in the relevant endpoint files.

## TimescaleDB vs Postgres

The service automatically detects if TimescaleDB is available:

- **With TimescaleDB**: `price_points` table is converted to a hypertable for optimized timeseries queries
- **Without TimescaleDB**: Falls back to regular Postgres table with proper indexes

The migration script handles both cases gracefully.

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

