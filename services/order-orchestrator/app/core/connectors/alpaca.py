"""Alpaca mock connector"""
import logging
import uuid
from typing import Optional
from app.core.connectors.base import BaseBrokerConnector, OrderResult

logger = logging.getLogger(__name__)


class AlpacaMockConnector(BaseBrokerConnector):
    """Mock Alpaca broker connector with deterministic behavior"""
    
    def __init__(self, config: dict):
        super().__init__("alpaca-mock", config)
        self._order_counter = 0
    
    async def place_order(
        self,
        instrument_id: int,
        qty: float,
        side: str,
        price_limit: Optional[float] = None
    ) -> OrderResult:
        """Place order with Alpaca (mock)"""
        # Generate external order ID
        self._order_counter += 1
        ext_order_id = f"ALPACA-{self._order_counter}-{uuid.uuid4().hex[:8].upper()}"
        
        # Check for simulated fill
        simulated_fill = self.get_simulated_fill(instrument_id)
        
        if simulated_fill:
            # Return filled order
            return OrderResult(
                success=True,
                ext_order_id=ext_order_id,
                status="filled",
                fill_price=simulated_fill["fill_price"],
                fill_qty=simulated_fill["fill_qty"]
            )
        
        # Default: Return placed order
        # In production, this would make actual API call to Alpaca
        logger.info(f"Alpaca order placed: {ext_order_id} for {qty} {side} @ {price_limit or 'MARKET'}")
        
        return OrderResult(
            success=True,
            ext_order_id=ext_order_id,
            status="placed"
        )
    
    async def get_order_status(self, ext_order_id: str) -> OrderResult:
        """Get order status from Alpaca (mock)"""
        # In production, this would query Alpaca API
        # For mock, return acked status
        return OrderResult(
            success=True,
            ext_order_id=ext_order_id,
            status="acked"
        )

