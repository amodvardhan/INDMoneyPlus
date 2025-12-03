"""Tests for price endpoints"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.models.instrument import Instrument


@pytest.mark.asyncio
async def test_get_latest_price(client: AsyncClient, test_instrument: Instrument):
    """Test getting latest price"""
    response = await client.get(
        f"/api/v1/price/{test_instrument.ticker}/latest",
        params={"exchange": test_instrument.exchange}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == test_instrument.ticker
    assert "price" in data
    assert "timestamp" in data
    assert "open" in data
    assert "high" in data
    assert "low" in data
    assert "close" in data


@pytest.mark.asyncio
async def test_get_price_timeseries(client: AsyncClient, test_instrument: Instrument):
    """Test getting price timeseries"""
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=7)
    
    response = await client.get(
        f"/api/v1/prices/{test_instrument.ticker}",
        params={
            "exchange": test_instrument.exchange,
            "from": from_date.isoformat(),
            "to": to_date.isoformat()
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == test_instrument.ticker
    assert "data" in data
    assert "count" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_price_nonexistent_instrument(client: AsyncClient):
    """Test getting price for non-existent instrument"""
    response = await client.get(
        "/api/v1/price/INVALID/latest",
        params={"exchange": "NSE"}
    )
    assert response.status_code == 404

