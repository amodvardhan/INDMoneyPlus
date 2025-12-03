"""Tests for ingestion endpoints"""
import pytest
from httpx import AsyncClient
from app.models.aggregator import BrokerAccount, RawStatement, NormalizedHolding


@pytest.mark.asyncio
async def test_ingest_csv_success(client: AsyncClient, test_account: BrokerAccount):
    """Test successful CSV ingestion"""
    csv_content = """Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00
TCS,INE467B01029,NSE,50,3500.75,175037.50"""
    
    files = {"file": ("holdings.csv", csv_content.encode(), "text/csv")}
    data = {"account_id": str(test_account.id)}
    
    response = await client.post(
        "/api/v1/ingest/csv",
        files=files,
        data=data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == test_account.id
    assert data["records_processed"] == 2
    assert data["holdings_created"] == 2


@pytest.mark.asyncio
async def test_ingest_csv_idempotency(client: AsyncClient, test_account: BrokerAccount):
    """Test CSV ingestion idempotency"""
    csv_content = """Ticker,ISIN,Exchange,Quantity,Avg Price,Current Value
RELIANCE,INE002A01018,NSE,100,2500.50,255000.00"""
    
    files = {"file": ("holdings.csv", csv_content.encode(), "text/csv")}
    data = {"account_id": str(test_account.id)}
    
    # First ingestion
    response1 = await client.post("/api/v1/ingest/csv", files=files, data=data)
    assert response1.status_code == 200
    
    # Second ingestion (should fail)
    response2 = await client.post("/api/v1/ingest/csv", files=files, data=data)
    assert response2.status_code == 409
    assert "already been processed" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_ingest_email(client: AsyncClient, test_account: BrokerAccount):
    """Test email ingestion"""
    request_data = {
        "account_id": test_account.id,
        "email_subject": "Portfolio Statement",
        "payload_json": {
            "holdings": [
                {"ticker": "RELIANCE", "qty": 100, "avg_price": 2500.50}
            ]
        }
    }
    
    response = await client.post("/api/v1/ingest/email", json=request_data)
    assert response.status_code == 200
    assert "statement_id" in response.json()


@pytest.mark.asyncio
async def test_ingest_broker_api(client: AsyncClient, test_account: BrokerAccount):
    """Test broker API ingestion"""
    request_data = {
        "account_id": test_account.id,
        "broker_name": "Zerodha",
        "holdings": [
            {
                "ticker": "RELIANCE",
                "exchange": "NSE",
                "qty": 100,
                "avg_price": 2500.50,
                "valuation": 255000.00
            }
        ]
    }
    
    response = await client.post("/api/v1/ingest/api/broker", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["holdings_created"] == 1

