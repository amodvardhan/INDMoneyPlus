"""Base adapter interface for market data providers"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.schemas.market_data import PricePointRead, LatestPriceResponse, StockFundamentals


class MarketDataAdapter(ABC):
    """Abstract base class for market data adapters"""
    
    @abstractmethod
    async def get_latest_price(self, ticker: str, exchange: str) -> Optional[LatestPriceResponse]:
        """Get the latest price for a ticker"""
        pass
    
    @abstractmethod
    async def get_historical_prices(
        self,
        ticker: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[PricePointRead]:
        """Get historical price data for a ticker"""
        pass
    
    @abstractmethod
    async def search_instruments(self, query: str) -> List[dict]:
        """Search for instruments by name or ticker"""
        pass
    
    async def get_fundamentals(self, ticker: str, exchange: str) -> Optional[StockFundamentals]:
        """Get stock fundamentals (market cap, P/E ratio, dividend yield, etc.) - Optional implementation"""
        return None

