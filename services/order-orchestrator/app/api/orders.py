"""Order endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.database import get_db
from app.models.order import Order, OrderBatch
from app.schemas.order import (
    OrderBatchCreate,
    OrderBatchResponse,
    OrderRead,
    SimulateFillRequest,
)
from app.core.validation.order_validator import OrderValidator, ValidationError
from app.core.idempotency import check_idempotency, store_idempotency, generate_idempotency_key
from app.core.connectors.factory import get_connector, get_routing_strategy
from app.core.order_lifecycle import update_order_status, process_order_fill
from app.core.events import publish_order_event

router = APIRouter()


@router.post("/orders", response_model=OrderBatchResponse)
async def create_order_batch(
    batch: OrderBatchCreate,
    db: AsyncSession = Depends(get_db),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    """Create order batch with idempotency support"""
    # Use provided idempotency key or generate one
    key = idempotency_key or generate_idempotency_key(batch.dict())
    
    # Check idempotency
    cached_response = await check_idempotency(key)
    if cached_response:
        return OrderBatchResponse(**cached_response)
    
    # Validate all orders
    validated_orders = []
    for order in batch.orders:
        try:
            OrderValidator.validate(order, batch.portfolio_id)
            validated_orders.append(order)
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order validation failed: {str(e)}"
            )
    
    # Get routing strategy
    routing = get_routing_strategy(validated_orders)
    
    # Create order batch
    order_batch = OrderBatch(
        user_id=1,  # Would come from auth in production
        portfolio_id=batch.portfolio_id,
        orders_json=[o.dict() for o in validated_orders],
        status="pending",
        idempotency_key=key
    )
    db.add(order_batch)
    await db.commit()
    await db.refresh(order_batch)
    
    # Create orders and place with brokers
    created_orders = []
    for i, order_data in enumerate(validated_orders):
        route = routing[i]
        broker = route["broker"]
        
        # Get connector
        connector = get_connector(broker)
        
        # Place order
        result = await connector.place_order(
            instrument_id=order_data.instrument_id,
            qty=order_data.qty,
            side=order_data.side,
            price_limit=order_data.price_limit
        )
        
        # Create order record
        order = Order(
            portfolio_id=batch.portfolio_id,
            broker=broker,
            instrument_id=order_data.instrument_id,
            qty=order_data.qty,
            price_limit=order_data.price_limit,
            side=order_data.side,
            status=result.status,
            ext_order_id=result.ext_order_id,
            batch_id=order_batch.id,
            fill_price=result.fill_price,
            fill_qty=result.fill_qty
        )
        db.add(order)
        await db.flush()
        
        # Update status if filled
        if result.status == "filled":
            order.executed_at = result.timestamp
        
        created_orders.append(order)
        
        # Publish event
        await publish_order_event(
            "order.placed",
            {
                "order_id": order.id,
                "batch_id": order_batch.id,
                "portfolio_id": batch.portfolio_id,
                "broker": broker,
                "instrument_id": order_data.instrument_id,
                "qty": order_data.qty,
                "side": order_data.side,
                "status": result.status,
                "ext_order_id": result.ext_order_id,
                "timestamp": result.timestamp.isoformat()
            }
        )
    
    await db.commit()
    
    # Update batch status
    order_batch.status = "processing"
    await db.commit()
    
    # Build response
    response = OrderBatchResponse(
        batch_id=order_batch.id,
        status=order_batch.status,
        orders=[OrderRead.model_validate(o) for o in created_orders],
        proposed_routing=routing,
        message=f"Batch {order_batch.id} created with {len(created_orders)} orders"
    )
    
    # Store for idempotency
    await store_idempotency(key, response.dict())
    
    return response


@router.get("/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get order status"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    return OrderRead.model_validate(order)


@router.post("/orders/{order_id}/simulate_fill")
async def simulate_fill(
    order_id: int,
    fill_request: SimulateFillRequest,
    db: AsyncSession = Depends(get_db)
):
    """Simulate order fills for testing"""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    
    # Find fill data for this order
    fill_data = None
    for fill in fill_request.fills:
        if fill.get("order_id") == order_id:
            fill_data = fill
            break
    
    if not fill_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No fill data found for order {order_id}"
        )
    
    fill_price = fill_data.get("fill_price")
    fill_qty = fill_data.get("fill_qty", order.qty)
    
    if not fill_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="fill_price is required"
        )
    
    # Process fill
    await process_order_fill(db, order_id, fill_price, fill_qty)
    
    return {
        "order_id": order_id,
        "status": "filled",
        "fill_price": fill_price,
        "fill_qty": fill_qty,
        "message": "Fill simulated successfully"
    }

