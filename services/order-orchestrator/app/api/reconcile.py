"""Reconciliation endpoint"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.order import Order, OrderBatch
from app.schemas.order import ReconciliationReport, OrderRead

router = APIRouter()


@router.get("/reconcile/{batch_id}", response_model=ReconciliationReport)
async def reconcile_batch(
    batch_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate reconciliation report for a batch"""
    # Get batch
    result = await db.execute(select(OrderBatch).where(OrderBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch {batch_id} not found"
        )
    
    # Get all orders in batch
    result = await db.execute(select(Order).where(Order.batch_id == batch_id))
    orders = result.scalars().all()
    
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No orders found for batch {batch_id}"
        )
    
    # Calculate statistics
    total_orders = len(orders)
    filled_orders = sum(1 for o in orders if o.status == "filled")
    pending_orders = sum(1 for o in orders if o.status in ["placed", "acked"])
    cancelled_orders = sum(1 for o in orders if o.status == "cancelled")
    
    total_qty = sum(o.qty for o in orders)
    filled_qty = sum(o.fill_qty or 0 for o in orders if o.status == "filled")
    
    # Calculate values
    total_value = sum((o.price_limit or 0) * o.qty for o in orders)
    filled_value = sum((o.fill_price or 0) * (o.fill_qty or 0) for o in orders if o.status == "filled")
    
    # Calculate P&L (simplified: difference between expected and actual)
    buy_orders = [o for o in orders if o.side == "BUY" and o.status == "filled"]
    sell_orders = [o for o in orders if o.side == "SELL" and o.status == "filled"]
    
    expected_pnl = None
    actual_pnl = None
    
    if buy_orders and sell_orders:
        # Simple P&L calculation: (sell_value - buy_value)
        buy_value = sum((o.fill_price or 0) * (o.fill_qty or 0) for o in buy_orders)
        sell_value = sum((o.fill_price or 0) * (o.fill_qty or 0) for o in sell_orders)
        actual_pnl = sell_value - buy_value
        
        # Expected P&L based on price limits
        expected_buy_value = sum((o.price_limit or 0) * o.qty for o in buy_orders)
        expected_sell_value = sum((o.price_limit or 0) * o.qty for o in sell_orders)
        expected_pnl = expected_sell_value - expected_buy_value
    
    return ReconciliationReport(
        batch_id=batch_id,
        total_orders=total_orders,
        filled_orders=filled_orders,
        pending_orders=pending_orders,
        cancelled_orders=cancelled_orders,
        total_qty=total_qty,
        filled_qty=filled_qty,
        total_value=total_value,
        filled_value=filled_value,
        expected_pnl=expected_pnl,
        actual_pnl=actual_pnl,
        orders=[OrderRead.model_validate(o) for o in orders]
    )

