"""Order orchestrator service tool adapter"""
import httpx
import logging
from typing import Dict, Any
from app.core.tools.base import BaseTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrderTool(BaseTool):
    """Tool for interacting with order orchestrator service"""
    
    def __init__(self):
        super().__init__("order-orchestrator", settings.order_orchestrator_url)
    
    async def call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP call to order orchestrator service"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=kwargs.get("params"))
                elif method.upper() == "POST":
                    response = await client.post(url, json=kwargs.get("json"))
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "data": data,
                    "citation": self._create_citation(endpoint, "order")
                }
        except Exception as e:
            logger.error(f"OrderTool error: {e}")
            raise
    
    async def validate_order_envelope(self, order_envelope: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order envelope before execution"""
        return await self.call(
            "POST",
            "/api/v1/orders/validate",
            json={"order_envelope": order_envelope}
        )

