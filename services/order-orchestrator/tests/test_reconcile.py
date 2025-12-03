"""Tests for reconciliation endpoint"""
import pytest
from httpx import AsyncClient
from app.models.order import Order, OrderBatch


@pytest.mark.asyncio
async def test_reconcile_batch(client: AsyncClient, db_session):
    """Test reconciliation report"""
    # Create batch
    batch = OrderBatch(
        user_id=1,
        portfolio_id=1,
        orders_json=[{"instrument_id": 1, "qty": 100, "side": "BUY"}],
        status="processing"
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)
    
    # Create orders
    buy_order = Order(
        portfolio_id=1,
        broker="zerodha-mock",
        instrument_id=1,
        qty=100,
        side="BUY",
        status="filled",
        fill_price=2500.0,
        fill_qty=100,
        batch_id=batch.id
    )
    
    sell_order = Order(
        portfolio_id=1,
        broker="alpaca-mock",
        instrument_id=2,
        qty=50,
        side="SELL",
        status="filled",
        fill_price=2600.0,
        fill_qty=50,
        batch_id=batch.id
    )
    
    db_session.add(buy_order)
    db_session.add(sell_order)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/reconcile/{batch.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["batch_id"] == batch.id
    assert data["total_orders"] == 2
    assert data["filled_orders"] == 2
    assert data["actual_pnl"] is not None

