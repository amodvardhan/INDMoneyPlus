"""Tests for instrument endpoints"""
import pytest
from httpx import AsyncClient
from app.models.instrument import Instrument


@pytest.mark.asyncio
async def test_create_instrument(client: AsyncClient):
    """Test creating a new instrument"""
    response = await client.post(
        "/api/v1/instruments",
        json={
            "ticker": "TCS",
            "exchange": "NSE",
            "name": "Tata Consultancy Services Ltd",
            "asset_class": "EQUITY",
            "timezone": "Asia/Kolkata"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ticker"] == "TCS"
    assert data["exchange"] == "NSE"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_instrument(client: AsyncClient, test_instrument: Instrument):
    """Test getting an instrument by ticker and exchange"""
    response = await client.get(
        f"/api/v1/instruments/{test_instrument.ticker}",
        params={"exchange": test_instrument.exchange}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == test_instrument.ticker
    assert data["exchange"] == test_instrument.exchange


@pytest.mark.asyncio
async def test_list_instruments(client: AsyncClient, test_instrument: Instrument):
    """Test listing instruments"""
    response = await client.get("/api/v1/instruments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_instruments_with_search(client: AsyncClient, test_instrument: Instrument):
    """Test listing instruments with search"""
    response = await client.get(
        "/api/v1/instruments",
        params={"search": "Reliance"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(inst["ticker"] == "RELIANCE" for inst in data)

