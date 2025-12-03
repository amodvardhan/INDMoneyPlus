"""Order lifecycle management"""
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order
from app.core.events import publish_order_event
from app.core.connectors.factory import get_connector

logger = logging.getLogger(__name__)


async def update_order_status(
    db: AsyncSession,
    order_id: int,
    new_status: str,
    fill_price: Optional[float] = None,
    fill_qty: Optional[float] = None,
    ext_order_id: Optional[str] = None
):
    """
    Update order status and publish event
    
    Args:
        db: Database session
        order_id: Order ID
        new_status: New status (placed, acked, filled, settled, cancelled, rejected)
        fill_price: Fill price (for filled orders)
        fill_qty: Fill quantity (for filled orders)
        ext_order_id: External order ID
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise ValueError(f"Order {order_id} not found")
    
    old_status = order.status
    order.status = new_status
    
    if fill_price is not None:
        order.fill_price = fill_price
    if fill_qty is not None:
        order.fill_qty = fill_qty
    if ext_order_id is not None:
        order.ext_order_id = ext_order_id
    
    if new_status == "filled":
        order.executed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(order)
    
    # Publish event
    await publish_order_event(
        f"order.{new_status}",
        {
            "order_id": order.id,
            "portfolio_id": order.portfolio_id,
            "broker": order.broker,
            "instrument_id": order.instrument_id,
            "qty": order.qty,
            "side": order.side,
            "status": new_status,
            "old_status": old_status,
            "fill_price": fill_price,
            "fill_qty": fill_qty,
            "ext_order_id": ext_order_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    logger.info(f"Order {order_id} status updated: {old_status} -> {new_status}")


async def process_order_acknowledgment(db: AsyncSession, order_id: int):
    """Process order acknowledgment from broker"""
    await update_order_status(db, order_id, "acked")


async def process_order_fill(
    db: AsyncSession,
    order_id: int,
    fill_price: float,
    fill_qty: float
):
    """Process order fill"""
    await update_order_status(
        db,
        order_id,
        "filled",
        fill_price=fill_price,
        fill_qty=fill_qty
    )

