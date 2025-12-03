"""Analytics service tool adapter"""
import httpx
import logging
from typing import Dict, Any
from app.core.tools.base import BaseTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsTool(BaseTool):
    """Tool for interacting with analytics service"""
    
    def __init__(self):
        super().__init__("analytics-service", settings.analytics_service_url)
    
    async def call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP call to analytics service"""
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
                    "citation": self._create_citation(endpoint, "analytics")
                }
        except Exception as e:
            logger.error(f"AnalyticsTool error: {e}")
            raise
    
    async def compute_portfolio_metrics(self, holdings: list) -> Dict[str, Any]:
        """Compute portfolio metrics"""
        return await self.call(
            "POST",
            "/api/v1/portfolio/metrics",
            json={"holdings": holdings}
        )
    
    async def compute_xirr(self, transactions: list) -> Dict[str, Any]:
        """Compute XIRR for portfolio"""
        return await self.call(
            "POST",
            "/api/v1/portfolio/xirr",
            json={"transactions": transactions}
        )
    
    async def simulate_rebalance(
        self,
        current_holdings: list,
        target_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """Simulate rebalancing and return trade proposals"""
        return await self.call(
            "POST",
            "/api/v1/rebalance/simulate",
            json={
                "current_holdings": current_holdings,
                "target_allocation": target_allocation
            }
        )

