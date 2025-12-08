"""Tiingo adapter for real market data"""
import httpx
import logging
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.adapters.base import MarketDataAdapter
from app.schemas.market_data import PricePointRead, LatestPriceResponse

logger = logging.getLogger(__name__)


class TiingoAdapter(MarketDataAdapter):
    """Adapter that fetches real prices from Tiingo API with connection pooling"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tiingo.com"
        self.timeout = 15.0  # Increased timeout for reliability
        self.headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json"
        }
        # Create persistent HTTP client with connection pooling
        self._client: Optional[httpx.AsyncClient] = None
        self._client_lock = False  # Simple flag for client initialization
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create persistent HTTP client with connection pooling"""
        if self._client is None:
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                limits=limits,
                http2=True  # Enable HTTP/2 for better performance
            )
        return self._client
    
    async def close(self):
        """Close HTTP client connection"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _get_tiingo_ticker(self, ticker: str, exchange: str) -> str:
        """Convert ticker and exchange to Tiingo format"""
        ticker_upper = ticker.upper()
        exchange_upper = exchange.upper()
        
        # Tiingo uses exchange prefix for Indian stocks
        # For NSE/BSE, format is "NSE:TICKER" or "BSE:TICKER"
        if exchange_upper in ["NSE", "BSE"]:
            # Tiingo requires exchange prefix for Indian stocks
            return f"{exchange_upper}:{ticker_upper}"
        else:
            # For other exchanges (NASDAQ, NYSE), use as-is
            return ticker_upper
    
    async def get_latest_price(self, ticker: str, exchange: str) -> Optional[LatestPriceResponse]:
        """Get latest price from Tiingo API with retry logic"""
        symbol = self._get_tiingo_ticker(ticker, exchange)
        max_retries = 2
        
        try:
            client = await self._get_client()
            
            # Tiingo daily prices endpoint (returns latest price)
            url = f"{self.base_url}/tiingo/daily/{symbol}/prices"
            params = {
                "token": self.api_key
            }
            
            for attempt in range(max_retries + 1):
                try:
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 404:
                        # Try without exchange prefix for NSE/BSE
                        if exchange.upper() in ["NSE", "BSE"]:
                            symbol_alt = ticker.upper()
                            url_alt = f"{self.base_url}/tiingo/daily/{symbol_alt}/prices"
                            response = await client.get(url_alt, params=params)
                    
                    response.raise_for_status()
                    data = response.json()
                    break  # Success, exit retry loop
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit
                        if attempt < max_retries:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Rate limited, retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    raise
                except httpx.TimeoutException:
                    if attempt < max_retries:
                        logger.warning(f"Timeout, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(1)
                        continue
                    raise
            
            if not data or len(data) == 0:
                logger.warning(f"No data from Tiingo for {symbol}")
                return None
            
            # Get the latest entry (first in the array, as Tiingo returns most recent first)
            latest = data[0]
            
            current_price = float(latest.get("close", latest.get("adjClose", 0)))
            previous_close = float(latest.get("prevClose", current_price))
            
            # Calculate change percent
            change_percent = ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0
            
            # Parse timestamp
            date_str = latest.get("date")
            if date_str:
                try:
                    price_timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    price_timestamp = datetime.utcnow()
            else:
                price_timestamp = datetime.utcnow()
            
            logger.info(f"Tiingo price for {symbol}: {current_price} (previous: {previous_close})")
            
            return LatestPriceResponse(
                ticker=ticker.upper(),
                exchange=exchange.upper(),
                price=round(current_price, 2),
                timestamp=price_timestamp,
                open=round(float(latest.get("open", current_price)), 2),
                high=round(float(latest.get("high", current_price)), 2),
                low=round(float(latest.get("low", current_price)), 2),
                close=round(current_price, 2),
                volume=int(latest.get("volume", 0)),
                change_percent=round(change_percent, 2),
                data_source="tiingo"
            )
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching price for {ticker} from Tiingo: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {ticker} from Tiingo: {e}", exc_info=True)
            return None
    
    async def get_historical_prices(
        self,
        ticker: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[PricePointRead]:
        """Get historical prices from Tiingo API with retry logic"""
        symbol = self._get_tiingo_ticker(ticker, exchange)
        max_retries = 2
        
        try:
            # Format dates for Tiingo (YYYY-MM-DD)
            start_date = from_date.strftime("%Y-%m-%d")
            end_date = to_date.strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/tiingo/daily/{symbol}/prices"
            params = {
                "startDate": start_date,
                "endDate": end_date,
                "token": self.api_key
            }
            
            client = await self._get_client()
            data = None
            
            for attempt in range(max_retries + 1):
                try:
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 404:
                        # Try without exchange prefix for NSE/BSE
                        if exchange.upper() in ["NSE", "BSE"]:
                            symbol_alt = ticker.upper()
                            url_alt = f"{self.base_url}/tiingo/daily/{symbol_alt}/prices"
                            response = await client.get(url_alt, params=params)
                    
                    response.raise_for_status()
                    data = response.json()
                    break  # Success, exit retry loop
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:  # Rate limit
                        if attempt < max_retries:
                            wait_time = 2 ** attempt  # Exponential backoff
                            logger.warning(f"Rate limited, retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                    raise
                except httpx.TimeoutException:
                    if attempt < max_retries:
                        logger.warning(f"Timeout, retrying... (attempt {attempt + 1}/{max_retries + 1})")
                        await asyncio.sleep(1)
                        continue
                    raise
            
            if not data:
                return []
            
            price_points = []
            for entry in data:
                date_str = entry.get("date")
                if not date_str:
                    continue
                
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except:
                    continue
                
                if dt < from_date or dt > to_date:
                    continue
                
                close_price = float(entry.get("close", entry.get("adjClose", 0)))
                if close_price <= 0:
                    continue
                
                price_points.append(PricePointRead(
                    id=0,
                    instrument_id=0,  # Will be set by caller
                    timestamp=dt,
                    open=round(float(entry.get("open", close_price)), 2),
                    high=round(float(entry.get("high", close_price)), 2),
                    low=round(float(entry.get("low", close_price)), 2),
                    close=round(close_price, 2),
                    volume=int(entry.get("volume", 0))
                ))
            
            return price_points
            
        except Exception as e:
            logger.error(f"Error fetching historical prices for {ticker} from Tiingo: {e}", exc_info=True)
            return []
    
    async def search_instruments(self, query: str) -> List[dict]:
        """Search for instruments using Tiingo API"""
        try:
            url = f"{self.base_url}/tiingo/utilities/search"
            params = {
                "query": query,
                "token": self.api_key
            }
            
            client = await self._get_client()
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data if isinstance(data, list) else []
            
        except Exception as e:
            logger.error(f"Error searching instruments on Tiingo: {e}")
            return []


