"""Tests for holdings endpoints"""
import pytest
from httpx import AsyncClient
from app.models.aggregator import BrokerAccount, NormalizedHolding


@pytest.mark.asyncio
async def test_get_consolidated_holdings(client: AsyncClient, db_session):
    """Test getting consolidated holdings"""
    # Create accounts
    account1 = BrokerAccount(
        user_id=1,
        broker_name="Zerodha",
        external_account_id="ZR123"
    )
    account2 = BrokerAccount(
        user_id=1,
        broker_name="ICICI",
        external_account_id="IC456"
    )
    db_session.add(account1)
    db_session.add(account2)
    await db_session.commit()
    await db_session.refresh(account1)
    await db_session.refresh(account2)
    
    # Create holdings
    holding1 = NormalizedHolding(
        account_id=account1.id,
        ticker="RELIANCE",
        exchange="NSE",
        qty=100,
        avg_price=2500.50,
        valuation=255000.00,
        source="csv"
    )
    holding2 = NormalizedHolding(
        account_id=account2.id,
        ticker="RELIANCE",
        exchange="NSE",
        qty=50,
        avg_price=2500.00,
        valuation=127500.00,
        source="api"
    )
    db_session.add(holding1)
    db_session.add(holding2)
    await db_session.commit()
    
    # Get consolidated holdings
    response = await client.get("/api/v1/holdings/1")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 1
    assert len(data["holdings"]) == 1  # Consolidated
    assert data["holdings"][0]["total_qty"] == 150.0  # 100 + 50
    assert len(data["holdings"][0]["accounts"]) == 2


@pytest.mark.asyncio
async def test_get_consolidated_holdings_empty(client: AsyncClient):
    """Test getting holdings for user with no accounts"""
    response = await client.get("/api/v1/holdings/999")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 999
    assert len(data["holdings"]) == 0

