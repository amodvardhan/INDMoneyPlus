"""Aggregator service tool adapter"""
import httpx
import logging
from typing import Dict, Any
from app.core.tools.base import BaseTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class AggregatorTool(BaseTool):
    """Tool for interacting with aggregator service"""
    
    def __init__(self):
        super().__init__("aggregator-service", settings.aggregator_service_url)
    
    async def call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP call to aggregator service"""
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
                    "citation": self._create_citation(endpoint, "aggregator")
                }
        except Exception as e:
            logger.error(f"AggregatorTool error: {e}")
            raise
    
    async def get_consolidated_holdings(self, user_id: int) -> Dict[str, Any]:
        """Get consolidated holdings for a user"""
        return await self.call(
            "GET",
            f"/api/v1/holdings/{user_id}"
        )

