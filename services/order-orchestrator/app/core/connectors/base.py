"""Base broker connector interface"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderResult:
    """Result from broker order placement"""
    success: bool
    ext_order_id: Optional[str] = None
    status: str = "placed"  # placed, acked, filled, rejected
    fill_price: Optional[float] = None
    fill_qty: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class BaseBrokerConnector(ABC):
    """Base class for broker connectors"""
    
    def __init__(self, broker_name: str, config: Dict[str, Any]):
        self.broker_name = broker_name
        self.config = config
        self._simulated_fills: Dict[int, Dict[str, Any]] = {}  # order_id -> fill data
    
    @abstractmethod
    async def place_order(
        self,
        instrument_id: int,
        qty: float,
        side: str,
        price_limit: Optional[float] = None
    ) -> OrderResult:
        """
        Place an order with the broker
        
        Args:
            instrument_id: Instrument ID
            qty: Quantity
            side: BUY or SELL
            price_limit: Optional price limit
            
        Returns:
            OrderResult with order details
        """
        pass
    
    @abstractmethod
    async def get_order_status(self, ext_order_id: str) -> OrderResult:
        """Get order status from broker"""
        pass
    
    def set_simulated_fill(self, order_id: int, fill_price: float, fill_qty: float):
        """Set simulated fill for testing"""
        self._simulated_fills[order_id] = {
            "fill_price": fill_price,
            "fill_qty": fill_qty
        }
    
    def get_simulated_fill(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get simulated fill data"""
        return self._simulated_fills.get(order_id)

