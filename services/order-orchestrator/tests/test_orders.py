"""Tests for order endpoints"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_create_order_batch(client: AsyncClient):
    """Test creating an order batch"""
    with patch("app.core.events.publish_order_event") as mock_event, \
         patch("app.core.idempotency.check_idempotency") as mock_idempotency:
        
        mock_idempotency.return_value = None
        
        response = await client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": 1,
                "orders": [
                    {
                        "instrument_id": 1,
                        "qty": 100,
                        "side": "BUY",
                        "price_limit": 2500.0
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert "orders" in data
        assert len(data["orders"]) == 1
        assert data["orders"][0]["side"] == "BUY"


@pytest.mark.asyncio
async def test_get_order(client: AsyncClient, db_session):
    """Test getting order status"""
    from app.models.order import Order
    
    order = Order(
        portfolio_id=1,
        broker="zerodha-mock",
        instrument_id=1,
        qty=100,
        side="BUY",
        status="placed",
        ext_order_id="ZERODHA-123"
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    
    response = await client.get(f"/api/v1/orders/{order.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order.id
    assert data["status"] == "placed"


@pytest.mark.asyncio
async def test_simulate_fill(client: AsyncClient, db_session):
    """Test simulating order fill"""
    from app.models.order import Order
    
    order = Order(
        portfolio_id=1,
        broker="zerodha-mock",
        instrument_id=1,
        qty=100,
        side="BUY",
        status="placed"
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)
    
    with patch("app.core.events.publish_order_event") as mock_event:
        response = await client.post(
            f"/api/v1/orders/{order.id}/simulate_fill",
            json={
                "fills": [
                    {
                        "order_id": order.id,
                        "fill_price": 2500.0,
                        "fill_qty": 100
                    }
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "filled"
        assert data["fill_price"] == 2500.0


@pytest.mark.asyncio
async def test_idempotency(client: AsyncClient):
    """Test idempotency key support"""
    with patch("app.core.idempotency.check_idempotency") as mock_check, \
         patch("app.core.events.publish_order_event") as mock_event:
        
        # First request
        mock_check.return_value = None
        
        response1 = await client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": 1,
                "orders": [{"instrument_id": 1, "qty": 100, "side": "BUY"}]
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response1.status_code == 200
        batch_id_1 = response1.json()["batch_id"]
        
        # Second request with same key
        cached_response = {
            "batch_id": batch_id_1,
            "status": "processing",
            "orders": [],
            "proposed_routing": [],
            "message": "Cached response"
        }
        mock_check.return_value = cached_response
        
        response2 = await client.post(
            "/api/v1/orders",
            json={
                "portfolio_id": 1,
                "orders": [{"instrument_id": 1, "qty": 100, "side": "BUY"}]
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        assert response2.status_code == 200
        assert response2.json()["batch_id"] == batch_id_1

