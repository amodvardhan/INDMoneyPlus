"""Broker connector factory"""
import logging
from typing import Dict, Any
from app.core.connectors.zerodha import ZerodhaMockConnector
from app.core.connectors.alpaca import AlpacaMockConnector
from app.core.connectors.base import BaseBrokerConnector

logger = logging.getLogger(__name__)

# Global connector instances
_connectors: Dict[str, BaseBrokerConnector] = {}


def get_connector(broker_name: str, config: Dict[str, Any] = None) -> BaseBrokerConnector:
    """
    Get or create broker connector
    
    Args:
        broker_name: Broker name (zerodha-mock, alpaca-mock)
        config: Broker configuration
        
    Returns:
        Broker connector instance
    """
    if broker_name not in _connectors:
        if broker_name == "zerodha-mock":
            _connectors[broker_name] = ZerodhaMockConnector(config or {})
        elif broker_name == "alpaca-mock":
            _connectors[broker_name] = AlpacaMockConnector(config or {})
        else:
            raise ValueError(f"Unknown broker: {broker_name}")
    
    return _connectors[broker_name]


def get_routing_strategy(orders: list, preferred_broker: str = None) -> list:
    """
    Determine routing strategy for orders
    
    Args:
        orders: List of orders
        preferred_broker: Preferred broker if specified
        
    Returns:
        List of routing decisions: [(order_index, broker, reason)]
    """
    routing = []
    
    for i, order in enumerate(orders):
        if preferred_broker and preferred_broker in ["zerodha-mock", "alpaca-mock"]:
            broker = preferred_broker
            reason = "Preferred broker specified"
        else:
            # Default routing: alternate or based on instrument
            # For mock, use zerodha-mock for Indian instruments, alpaca-mock for US
            # This is a simple heuristic - in production, use more sophisticated routing
            broker = "zerodha-mock" if i % 2 == 0 else "alpaca-mock"
            reason = "Default routing strategy"
        
        routing.append({
            "order_index": i,
            "broker": broker,
            "reason": reason
        })
    
    return routing

