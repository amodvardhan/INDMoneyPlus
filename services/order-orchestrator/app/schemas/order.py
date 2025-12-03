"""Pydantic schemas for order orchestrator"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class OrderCreate(BaseModel):
    instrument_id: int
    qty: float = Field(..., gt=0, description="Quantity must be positive")
    price_limit: Optional[float] = Field(None, gt=0, description="Price limit for limit orders")
    side: str = Field(..., pattern="^(BUY|SELL)$", description="Order side: BUY or SELL")
    broker: Optional[str] = Field(None, description="Preferred broker (optional)")


class OrderRead(BaseModel):
    id: int
    portfolio_id: int
    broker: str
    instrument_id: int
    qty: float
    price_limit: Optional[float] = None
    side: str
    status: str
    created_at: datetime
    executed_at: Optional[datetime] = None
    ext_order_id: Optional[str] = None
    fill_price: Optional[float] = None
    fill_qty: Optional[float] = None
    batch_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class OrderBatchCreate(BaseModel):
    portfolio_id: int
    orders: List[OrderCreate] = Field(..., min_items=1, description="List of orders to batch")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate prevention")


class OrderBatchRead(BaseModel):
    id: int
    user_id: int
    portfolio_id: int
    orders_json: Dict[str, Any]
    status: str
    created_at: datetime
    idempotency_key: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProposedRouting(BaseModel):
    order_index: int
    broker: str
    reason: str


class OrderBatchResponse(BaseModel):
    batch_id: int
    status: str
    orders: List[OrderRead]
    proposed_routing: List[ProposedRouting]
    message: str


class SimulateFillRequest(BaseModel):
    fills: List[Dict[str, Any]] = Field(..., description="List of fill data: {order_id, fill_price, fill_qty}")


class ReconciliationReport(BaseModel):
    batch_id: int
    total_orders: int
    filled_orders: int
    pending_orders: int
    cancelled_orders: int
    total_qty: float
    filled_qty: float
    total_value: float
    filled_value: float
    expected_pnl: Optional[float] = None
    actual_pnl: Optional[float] = None
    orders: List[OrderRead]


class BrokerConnectorConfigRead(BaseModel):
    id: int
    broker_name: str
    config_json: Dict[str, Any]
    active: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

