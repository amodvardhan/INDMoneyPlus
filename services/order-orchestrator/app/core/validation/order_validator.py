"""Order validation rules"""
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Validation error"""
    pass


class OrderValidator:
    """Validates orders before processing"""
    
    @staticmethod
    def validate(order: OrderCreate, portfolio_id: int, instrument_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate an order
        
        Args:
            order: Order to validate
            portfolio_id: Portfolio ID
            instrument_data: Optional instrument data for validation
            
        Returns:
            Dict with validation result
            
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Lot size validation
        if order.qty < settings.min_lot_size:
            errors.append(f"Quantity {order.qty} is below minimum lot size {settings.min_lot_size}")
        
        # Price limit validation
        if order.price_limit is not None:
            if order.price_limit <= 0:
                errors.append("Price limit must be positive")
            
            # Check if price limit is reasonable (not too high)
            estimated_value = order.qty * order.price_limit
            if estimated_value > settings.max_order_value:
                errors.append(f"Order value {estimated_value} exceeds maximum {settings.max_order_value}")
        
        # Side validation
        if order.side not in ["BUY", "SELL"]:
            errors.append(f"Invalid side: {order.side}. Must be BUY or SELL")
        
        # Margin check (mock)
        if settings.margin_check_enabled:
            margin_result = OrderValidator._check_margin(order, portfolio_id)
            if not margin_result["valid"]:
                errors.append(margin_result["reason"])
        
        # Instrument-specific validation
        if instrument_data:
            if "lot_size" in instrument_data:
                lot_size = instrument_data["lot_size"]
                if order.qty % lot_size != 0:
                    errors.append(f"Quantity {order.qty} must be multiple of lot size {lot_size}")
        
        if errors:
            raise ValidationError("; ".join(errors))
        
        return {
            "valid": True,
            "estimated_value": order.qty * (order.price_limit or 0)
        }
    
    @staticmethod
    def _check_margin(order: OrderCreate, portfolio_id: int) -> Dict[str, Any]:
        """
        Mock margin check
        
        In production, this would check:
        - Available margin
        - Position limits
        - Risk limits
        """
        # Mock: Always pass for now
        # In production, query portfolio margin and validate
        estimated_value = order.qty * (order.price_limit or 1000.0)  # Mock price
        
        # Mock margin limit: 1M
        margin_limit = 1000000.0
        
        if estimated_value > margin_limit:
            return {
                "valid": False,
                "reason": f"Insufficient margin. Required: {estimated_value}, Available: {margin_limit}"
            }
        
        return {"valid": True}

