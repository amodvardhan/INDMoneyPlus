"""Market data service tool adapter"""
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.tools.base import BaseTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class MarketDataTool(BaseTool):
    """Tool for interacting with market data service"""
    
    def __init__(self):
        super().__init__("marketdata-service", settings.marketdata_service_url)
    
    async def call(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP call to market data service"""
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
                    "citation": self._create_citation(endpoint, "market_data")
                }
        except Exception as e:
            logger.error(f"MarketDataTool error: {e}")
            raise
    
    async def get_latest_price(self, ticker: str, exchange: str) -> Dict[str, Any]:
        """Get latest price for a ticker"""
        return await self.call(
            "GET",
            f"/api/v1/price/{ticker}/latest",
            params={"exchange": exchange}
        )
    
    async def get_price_timeseries(
        self,
        ticker: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime
    ) -> Dict[str, Any]:
        """Get historical price timeseries"""
        return await self.call(
            "GET",
            f"/api/v1/prices/{ticker}",
            params={
                "exchange": exchange,
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }
        )
    
    async def get_instrument(self, ticker: str, exchange: str) -> Dict[str, Any]:
        """Get instrument details"""
        return await self.call(
            "GET",
            f"/api/v1/instruments/{ticker}",
            params={"exchange": exchange}
        )

    async def get_historical_prices(
        self,
        ticker: str,
        exchange: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get historical prices for a ticker"""
        from datetime import datetime, timedelta
        to_date = datetime.utcnow()
        from_date = to_date - timedelta(days=days)
        return await self.get_price_timeseries(ticker, exchange, from_date, to_date)

