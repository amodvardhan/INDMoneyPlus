# Aggregator Service

Production-ready service for aggregating holdings from multiple custodians/brokers via API, CAS/email/PDF ingestion, and manual CSV upload. Normalizes instruments (ISIN), reconciles holdings, and produces normalized position feed for analytics service.

## Features

- **Multi-Source Ingestion**: CSV upload, email/webhook, and broker API integration
- **Instrument Normalization**: ISIN/Ticker mapping with marketdata service integration
- **Idempotency**: Prevents duplicate statement processing
- **Holdings Consolidation**: Aggregates holdings across multiple accounts
- **Reconciliation**: Detects discrepancies and emits Kafka events
- **Flexible CSV Parsing**: Supports multiple column name formats with custom mapping

## Database Models

- **BrokerAccount**: `id`, `user_id`, `broker_name`, `external_account_id`, `metadata`, `created_at`, `updated_at`
- **RawStatement**: `id`, `account_id`, `content_type`, `payload_json`, `statement_hash`, `ingested_at`
- **NormalizedHolding**: `id`, `account_id`, `instrument_id`, `isin`, `ticker`, `exchange`, `qty`, `avg_price`, `valuation`, `source`, `updated_at`
- **ReconciliationException**: `id`, `account_id`, `message`, `payload_json`, `resolved`, `created_at`, `resolved_at`
- **InstrumentMapping**: `id`, `isin`, `ticker`, `exchange`, `instrument_id`, `broker_variant`, `created_at`

## API Endpoints

### Ingestion

- `POST /api/v1/ingest/csv` - Upload CSV file with holdings
  - Form data: `file` (CSV), `account_id` (int)
  - Response: `CSVUploadResponse`
  
- `POST /api/v1/ingest/email` - Ingest holdings from email/webhook
  - Request: `EmailIngestRequest`
  - Response: Statement ID
  
- `POST /api/v1/ingest/api/broker` - Ingest holdings from broker API
  - Request: `BrokerAPIIngestRequest`
  - Response: Statement ID and holdings count

### Holdings

- `GET /api/v1/holdings/{user_id}` - Get consolidated holdings across all accounts
  - Response: `HoldingsResponse` with consolidated holdings

### Health & Metrics

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

## Running Locally

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 15+
- Redis 7+
- Kafka (optional, for event streaming)

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
poetry run uvicorn app.main:app --reload --port 8002
```

### Using Docker Compose

```bash
cd services/aggregator-service
docker-compose -f docker-compose.dev.yml up --build
```

This will start:
- PostgreSQL on port 5432
- Redis on port 6379
- Kafka + Zookeeper on port 9092
- Aggregator service on port 8002

## CSV Format

The CSV parser supports flexible column naming. Standard column names are automatically detected:

### Standard Format

```csv
Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00
TCS,INE467B01029,NSE,50,3500.75,175037.50
```

### Alternate Format

```csv
Symbol,ISIN Code,Market,Shares,Cost Price,Market Value
AAPL,US0378331005,NASDAQ,25,150.00,3750.00
GOOGL,US02079K3059,NASDAQ,10,120.50,1205.00
```

### Supported Column Name Variations

- **Ticker**: `ticker`, `symbol`, `scrip`, `instrument`, `stock`
- **ISIN**: `isin`, `isincode`, `isin_code`
- **Exchange**: `exchange`, `bse`, `nse`, `market`
- **Quantity**: `qty`, `quantity`, `shares`, `units`, `balance`
- **Avg Price**: `avg_price`, `average_price`, `cost_price`, `purchase_price`, `buy_price`
- **Valuation**: `valuation`, `current_value`, `market_value`, `value`

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

- **test_csv_parser.py**: CSV parsing with various formats
- **test_ingest.py**: Ingestion endpoints (CSV, email, API)
- **test_holdings.py**: Holdings consolidation

## Manual Verification Steps

### 1. Create Broker Account

First, create a broker account (via API or directly in database):

```python
# Via API (if endpoint exists) or directly in database
account = BrokerAccount(
    user_id=1,
    broker_name="Zerodha",
    external_account_id="ZR123456"
)
```

### 2. Ingest CSV

```bash
curl -X POST "http://localhost:8002/api/v1/ingest/csv?account_id=1" \
  -F "file=@tests/fixtures/sample_holdings.csv"
```

**Expected**: `200 OK` with statement_id and holdings_created count

### 3. Verify Idempotency

```bash
# Upload same CSV again
curl -X POST "http://localhost:8002/api/v1/ingest/csv?account_id=1" \
  -F "file=@tests/fixtures/sample_holdings.csv"
```

**Expected**: `409 Conflict` with "already been processed" message

### 4. Ingest via Email/Webhook

```bash
curl -X POST "http://localhost:8002/api/v1/ingest/email" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "email_subject": "Portfolio Statement",
    "payload_json": {
      "holdings": [
        {"ticker": "RELIANCE", "exchange": "NSE", "qty": 100, "avg_price": 2500.50}
      ]
    }
  }'
```

**Expected**: `200 OK` with statement_id

### 5. Ingest via Broker API

```bash
curl -X POST "http://localhost:8002/api/v1/ingest/api/broker" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "broker_name": "Zerodha",
    "holdings": [
      {
        "ticker": "TCS",
        "exchange": "NSE",
        "qty": 50,
        "avg_price": 3500.75,
        "valuation": 175037.50
      }
    ]
  }'
```

**Expected**: `200 OK` with holdings_created count

### 6. Get Consolidated Holdings

```bash
curl "http://localhost:8002/api/v1/holdings/1"
```

**Expected**: `200 OK` with consolidated holdings across all accounts

### 7. Health Check

```bash
curl http://localhost:8002/health
```

**Expected**: `200 OK` with service status

### 8. Metrics

```bash
curl http://localhost:8002/metrics
```

**Expected**: `200 OK` with Prometheus metrics format

## Sample CSV Files

### Sample 1: Standard Format

```csv
Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00
TCS,INE467B01029,NSE,50,3500.75,175037.50
HDFCBANK,INE040A01034,NSE,200,1650.25,330050.00
INFY,INE009A01021,NSE,75,1450.00,108750.00
```

### Sample 2: Alternate Format

```csv
Symbol,ISIN Code,Market,Shares,Cost Price,Market Value
AAPL,US0378331005,NASDAQ,25,150.00,3750.00
GOOGL,US02079K3059,NASDAQ,10,120.50,1205.00
MSFT,US5949181045,NASDAQ,30,300.25,9007.50
```

These sample files are available in `tests/fixtures/` directory.

## Acceptance Criteria

✅ **Database Models**
- [x] BrokerAccount model with all required fields
- [x] RawStatement model with idempotency hash
- [x] NormalizedHolding model with instrument references
- [x] ReconciliationException model for discrepancy tracking
- [x] InstrumentMapping model for ISIN/Ticker normalization

✅ **CSV Parser**
- [x] Flexible column mapping (standard and alternate formats)
- [x] Custom column mapping support
- [x] Handles missing columns gracefully
- [x] Validates required fields (quantity)
- [x] Statement hash generation for idempotency

✅ **Instrument Normalization**
- [x] ISIN/Ticker mapping table
- [x] Integration with marketdata service
- [x] Automatic mapping creation
- [x] Caching for performance

✅ **Idempotency**
- [x] Redis-based idempotency checking
- [x] Statement hash generation
- [x] Prevents duplicate processing
- [x] Graceful failure if Redis unavailable

✅ **Ingestion Endpoints**
- [x] POST /api/v1/ingest/csv with file upload
- [x] POST /api/v1/ingest/email with webhook payload
- [x] POST /api/v1/ingest/api/broker with holdings JSON
- [x] Proper error handling and validation
- [x] Kafka event emission on successful ingestion

✅ **Holdings Consolidation**
- [x] GET /api/v1/holdings/{user_id} consolidates across accounts
- [x] Groups by instrument (ISIN/Ticker/Exchange)
- [x] Calculates total quantities
- [x] Weighted average price calculation
- [x] Total valuation aggregation

✅ **Reconciliation**
- [x] Reconciliation job detects discrepancies
- [x] Missing instrument mappings
- [x] Negative quantities
- [x] Missing valuations
- [x] Kafka event emission for exceptions

✅ **Observability**
- [x] Health check endpoint
- [x] Prometheus metrics endpoint
- [x] Proper logging

✅ **Testing**
- [x] Unit tests for CSV parser
- [x] Integration tests for ingestion endpoints
- [x] Tests for holdings consolidation
- [x] Sample CSV fixtures
- [x] Idempotency tests

✅ **DevOps**
- [x] Dockerfile for containerization
- [x] docker-compose.dev.yml with Postgres + Redis + Kafka
- [x] .env.example
- [x] Alembic migrations

## CSV Parsing Examples

### Example 1: Standard Format

```csv
Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00
```

**Result**: Parsed as ticker="RELIANCE", isin="INE002A01018", qty=100, avg_price=2500.50

### Example 2: Custom Mapping

```python
custom_mapping = {
    "ticker": "Stock",
    "qty": "Units",
    "avg_price": "Price"
}
parser = CSVParser(custom_mapping=custom_mapping)
```

### Example 3: Consolidation

If user has holdings in multiple accounts:
- Account 1: RELIANCE 100 shares @ 2500.50
- Account 2: RELIANCE 50 shares @ 2500.00

**Consolidated Result**: RELIANCE 150 shares @ 2500.33 (weighted average)

## Reconciliation

The reconciliation job runs periodically and checks for:
- Missing instrument mappings (ticker/ISIN not found in marketdata)
- Negative quantities
- Missing valuations for holdings with quantity > 0

Reconciliation exceptions are stored in the database and emitted as Kafka events for analytics service consumption.

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
