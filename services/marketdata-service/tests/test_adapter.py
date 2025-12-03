"""Tests for market data adapters"""
import pytest
from datetime import datetime, timedelta
from app.core.adapters.in_memory import InMemoryAdapter


@pytest.mark.asyncio
async def test_in_memory_adapter_get_latest_price():
    """Test InMemoryAdapter get_latest_price"""
    adapter = InMemoryAdapter()
    price = await adapter.get_latest_price("RELIANCE", "NSE")
    
    assert price is not None
    assert price.ticker == "RELIANCE"
    assert price.exchange == "NSE"
    assert price.price > 0
    assert price.open > 0
    assert price.high > 0
    assert price.low > 0
    assert price.close > 0


@pytest.mark.asyncio
async def test_in_memory_adapter_get_historical_prices():
    """Test InMemoryAdapter get_historical_prices"""
    adapter = InMemoryAdapter()
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=5)
    
    prices = await adapter.get_historical_prices("RELIANCE", "NSE", from_date, to_date)
    
    assert len(prices) > 0
    assert all(p.open > 0 for p in prices)
    assert all(p.high >= p.low for p in prices)


@pytest.mark.asyncio
async def test_in_memory_adapter_search_instruments():
    """Test InMemoryAdapter search_instruments"""
    adapter = InMemoryAdapter()
    results = await adapter.search_instruments("Apple")
    
    assert len(results) > 0
    assert any("AAPL" in inst["ticker"] for inst in results)

