"""In-memory market data adapter for development and testing"""
import random
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.adapters.base import MarketDataAdapter
from app.schemas.market_data import PricePointRead, LatestPriceResponse


class InMemoryAdapter(MarketDataAdapter):
    """In-memory adapter that generates synthetic price data using random walk algorithm"""
    
    def __init__(self, base_prices: Optional[dict] = None):
        """
        Initialize in-memory adapter with optional base prices.
        
        Args:
            base_prices: Dict mapping (ticker, exchange) to base price
        """
        self.base_prices = base_prices or {}
        self._price_cache = {}  # Cache current prices per ticker
    
    def _get_base_price(self, ticker: str, exchange: str) -> float:
        """Get base price for a ticker, generating if not exists"""
        key = (ticker.upper(), exchange.upper())
        if key not in self.base_prices:
            # Generate a synthetic base price between 10 and 1000
            self.base_prices[key] = round(random.uniform(10.0, 1000.0), 2)
        return self.base_prices[key]
    
    def _get_current_price(self, ticker: str, exchange: str) -> float:
        """Get current price with random walk algorithm"""
        key = (ticker.upper(), exchange.upper())
        base = self._get_base_price(ticker, exchange)
        
        if key not in self._price_cache:
            self._price_cache[key] = base
        
        # Random walk: change by -2% to +2%
        change_pct = random.uniform(-0.02, 0.02)
        self._price_cache[key] = max(0.01, self._price_cache[key] * (1 + change_pct))
        
        return round(self._price_cache[key], 2)
    
    async def get_latest_price(self, ticker: str, exchange: str) -> Optional[LatestPriceResponse]:
        """Get the latest price using synthetic data generation"""
        price = self._get_current_price(ticker, exchange)
        # Generate OHLC around the current price
        variation = price * 0.01  # 1% variation
        
        return LatestPriceResponse(
            ticker=ticker.upper(),
            exchange=exchange.upper(),
            price=price,
            timestamp=datetime.utcnow(),
            open=round(price - random.uniform(0, variation), 2),
            high=round(price + random.uniform(0, variation), 2),
            low=round(price - random.uniform(0, variation), 2),
            close=price,
            volume=random.randint(1000, 1000000)
        )
    
    async def get_historical_prices(
        self,
        ticker: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[PricePointRead]:
        """Generate synthetic historical price data using random walk"""
        base_price = self._get_base_price(ticker, exchange)
        prices = []
        current_date = from_date
        current_price = base_price
        
        # Generate daily OHLC data
        while current_date <= to_date:
            # Random walk for price movement
            change_pct = random.uniform(-0.05, 0.05)
            current_price = max(0.01, current_price * (1 + change_pct))
            
            variation = current_price * 0.02
            open_price = round(current_price + random.uniform(-variation, variation), 2)
            high_price = round(open_price + random.uniform(0, variation), 2)
            low_price = round(open_price - random.uniform(0, variation), 2)
            close_price = round(current_price, 2)
            
            prices.append(PricePointRead(
                id=0,
                instrument_id=0,
                timestamp=current_date,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=random.randint(1000, 1000000)
            ))
            
            current_date += timedelta(days=1)
        
        return prices
    
    async def search_instruments(self, query: str) -> List[dict]:
        """Search instruments from predefined catalog"""
        # Predefined instrument catalog
        instrument_catalog = [
            {
                "ticker": "AAPL",
                "exchange": "NASDAQ",
                "name": "Apple Inc.",
                "asset_class": "EQUITY"
            },
            {
                "ticker": "RELIANCE",
                "exchange": "NSE",
                "name": "Reliance Industries Ltd",
                "asset_class": "EQUITY"
            },
            {
                "ticker": "TCS",
                "exchange": "NSE",
                "name": "Tata Consultancy Services Ltd",
                "asset_class": "EQUITY"
            }
        ]
        
        query_lower = query.lower()
        return [
            inst for inst in instrument_catalog
            if query_lower in inst["ticker"].lower() or query_lower in inst["name"].lower()
        ]

