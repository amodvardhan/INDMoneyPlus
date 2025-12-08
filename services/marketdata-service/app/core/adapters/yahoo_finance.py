"""Yahoo Finance adapter for real market data"""
import logging
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from app.core.adapters.base import MarketDataAdapter
from app.schemas.market_data import PricePointRead, LatestPriceResponse, StockFundamentals

logger = logging.getLogger(__name__)


class YahooFinanceAdapter(MarketDataAdapter):
    """Adapter that fetches real prices from Yahoo Finance using yfinance library with optimized thread pool"""
    
    def __init__(self):
        # Use ThreadPoolExecutor to run yfinance (synchronous) in async context
        # Optimized pool size for better performance
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="yfinance")
        self._cache_timeout = 60  # Cache timeout in seconds for yfinance Ticker objects
    
    def _get_yahoo_symbol(self, ticker: str, exchange: str) -> str:
        """Convert ticker and exchange to Yahoo Finance symbol"""
        ticker_upper = ticker.upper()
        exchange_upper = exchange.upper()
        
        # Map exchanges to Yahoo Finance suffixes
        exchange_map = {
            "NSE": ".NS",  # NSE stocks
            "BSE": ".BO",  # BSE stocks
            "NASDAQ": "",  # No suffix for NASDAQ
            "NYSE": "",   # No suffix for NYSE
        }
        
        suffix = exchange_map.get(exchange_upper, "")
        return f"{ticker_upper}{suffix}"
    
    async def get_latest_price(self, ticker: str, exchange: str) -> Optional[LatestPriceResponse]:
        """Get latest price from Yahoo Finance using yfinance library"""
        symbol = self._get_yahoo_symbol(ticker, exchange)
        
        try:
            # Run yfinance in thread pool (it's synchronous)
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(self.executor, yf.Ticker, symbol)
            
            # Get history first (more reliable)
            hist = await loop.run_in_executor(
                self.executor, 
                lambda: ticker_obj.history(period="1d", interval="1d")
            )
            
            if hist.empty:
                logger.warning(f"No data from Yahoo Finance for {symbol}")
                return None
            
            # Get latest price from history
            latest_row = hist.iloc[-1]
            history_close = float(latest_row["Close"])
            
            # Try to get info (may fail or be None)
            info = None
            try:
                info = await loop.run_in_executor(self.executor, lambda: ticker_obj.info)
            except Exception as e:
                logger.debug(f"Could not fetch info for {symbol}: {e}")
                info = {}
            
            # Try multiple price fields from info, prioritizing regularMarketPrice
            # This is the most current price from Yahoo Finance
            current_price = None
            if info and isinstance(info, dict):
                current_price = (
                    info.get("regularMarketPrice") or 
                    info.get("currentPrice") or 
                    info.get("regularMarketPreviousClose") or
                    info.get("previousClose")
                )
                if current_price:
                    current_price = float(current_price)
            
            # Fall back to history close if info doesn't have price
            if current_price is None or current_price <= 0:
                current_price = history_close
                logger.debug(f"Using history close price for {symbol}: {current_price}")
            
            # Get previous close
            previous_close = None
            if info and isinstance(info, dict):
                previous_close = (
                    info.get("previousClose") or 
                    info.get("regularMarketPreviousClose")
                )
                if previous_close:
                    previous_close = float(previous_close)
            
            # Fall back to history close if no previous close in info
            if previous_close is None or previous_close <= 0:
                previous_close = history_close
            
            # Log all price-related fields for debugging
            logger.info(f"Yahoo Finance data for {symbol}:")
            if info and isinstance(info, dict):
                logger.info(f"  regularMarketPrice: {info.get('regularMarketPrice')}")
                logger.info(f"  currentPrice: {info.get('currentPrice')}")
                logger.info(f"  previousClose: {info.get('previousClose')}")
                logger.info(f"  currency: {info.get('currency', 'INR')}")
            logger.info(f"  history Close: {history_close}")
            logger.info(f"  Using price: {current_price}")
            
            # Calculate change percent
            change_percent = ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0
            
            # Get timestamp
            timestamp = latest_row.name if hasattr(latest_row.name, 'timestamp') else datetime.utcnow()
            if isinstance(timestamp, datetime):
                price_timestamp = timestamp
            else:
                price_timestamp = datetime.utcnow()
            
            return LatestPriceResponse(
                ticker=ticker.upper(),
                exchange=exchange.upper(),
                price=round(current_price, 2),
                timestamp=price_timestamp,
                open=round(float(latest_row["Open"]), 2),
                high=round(float(latest_row["High"]), 2),
                low=round(float(latest_row["Low"]), 2),
                close=round(current_price, 2),
                volume=int(latest_row["Volume"]) if not hist.empty else 0,
                change_percent=round(change_percent, 2),
                data_source="yahoo_finance"
            )
            
        except Exception as e:
            logger.error(f"Error fetching price for {ticker} from Yahoo Finance: {e}", exc_info=True)
            return None
    
    async def get_historical_prices(
        self,
        ticker: str,
        exchange: str,
        from_date: datetime,
        to_date: datetime
    ) -> List[PricePointRead]:
        """Get historical prices from Yahoo Finance using yfinance library"""
        try:
            symbol = self._get_yahoo_symbol(ticker, exchange)
            logger.info(f"📊 Fetching historical prices for {symbol} (ticker: {ticker}, exchange: {exchange}) from {from_date.date()} to {to_date.date()}")
            
            # Calculate period for yfinance
            days_diff = (to_date - from_date).days
            if days_diff <= 5:
                period = "5d"
            elif days_diff <= 30:
                period = "1mo"
            elif days_diff <= 90:
                period = "3mo"
            elif days_diff <= 180:
                period = "6mo"
            elif days_diff <= 365:
                period = "1y"
            else:
                period = "2y"
            
            logger.info(f"📅 Using yfinance period: {period} for {days_diff} days difference")
            
            # Run yfinance in thread pool
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(self.executor, yf.Ticker, symbol)
            hist = await loop.run_in_executor(
                self.executor,
                lambda: ticker_obj.history(period=period, interval="1d")
            )
            
            if hist.empty:
                logger.warning(f"⚠️  Empty history returned from yfinance for {symbol}. Period: {period}")
                return []
            
            logger.info(f"📈 Received {len(hist)} rows from yfinance for {symbol}")
            
            # Get actual date range from yfinance data
            if len(hist) > 0:
                actual_start = hist.index[0].to_pydatetime() if hasattr(hist.index[0], 'to_pydatetime') else None
                actual_end = hist.index[-1].to_pydatetime() if hasattr(hist.index[-1], 'to_pydatetime') else None
                logger.info(
                    f"📅 yfinance data range: {actual_start.date() if actual_start else 'N/A'} to {actual_end.date() if actual_end else 'N/A'}, "
                    f"Requested: {from_date.date()} to {to_date.date()}"
                )
            
            price_points = []
            for idx, row in hist.iterrows():
                dt = idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.utcnow()
                # Normalize dates to midnight for comparison (ignore time component)
                dt_date = dt.date()
                from_date_only = from_date.date()
                to_date_only = to_date.date()
                
                # For long periods (1y+), be more lenient with date filtering
                # Include data that's close to the requested range (within 7 days)
                days_before = (from_date_only - dt_date).days if dt_date < from_date_only else 0
                days_after = (dt_date - to_date_only).days if dt_date > to_date_only else 0
                
                # Allow 7 days tolerance for market holidays and weekends
                tolerance_days = 7
                if days_before > tolerance_days or days_after > tolerance_days:
                    continue
                
                price_points.append(PricePointRead(
                    id=0,
                    instrument_id=0,  # Will be set by caller
                    timestamp=dt,
                    open=round(float(row["Open"]), 2),
                    high=round(float(row["High"]), 2),
                    low=round(float(row["Low"]), 2),
                    close=round(float(row["Close"]), 2),
                    volume=int(row["Volume"]) if "Volume" in row else 0
                ))
            
            logger.info(f"✅ Filtered to {len(price_points)} price points within date range {from_date.date()} to {to_date.date()}")
            
            if len(price_points) == 0:
                logger.warning(
                    f"⚠️  No price points after filtering for {symbol}. "
                    f"History range: {hist.index[0].date() if len(hist) > 0 and hasattr(hist.index[0], 'date') else 'N/A'} to "
                    f"{hist.index[-1].date() if len(hist) > 0 and hasattr(hist.index[-1], 'date') else 'N/A'}, "
                    f"Requested range: {from_date.date()} to {to_date.date()}. "
                    f"Total rows from yfinance: {len(hist)}"
                )
                # If we have data from yfinance but filtered everything out, return all data anyway
                # This handles cases where date ranges don't match exactly
                if len(hist) > 0:
                    logger.info(f"🔄 Returning all {len(hist)} rows from yfinance despite date mismatch")
                    price_points = []
                    for idx, row in hist.iterrows():
                        dt = idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else datetime.utcnow()
                        price_points.append(PricePointRead(
                            id=0,
                            instrument_id=0,
                            timestamp=dt,
                            open=round(float(row["Open"]), 2),
                            high=round(float(row["High"]), 2),
                            low=round(float(row["Low"]), 2),
                            close=round(float(row["Close"]), 2),
                            volume=int(row["Volume"]) if "Volume" in row else 0
                        ))
            
            return price_points
            
        except Exception as e:
            logger.error(f"❌ Error fetching historical prices for {ticker} ({exchange}) from Yahoo Finance: {e}", exc_info=True)
            return []
    
    async def search_instruments(self, query: str) -> List[dict]:
        """Search for instruments (not implemented for Yahoo Finance)"""
        return []
    
    async def get_fundamentals(self, ticker: str, exchange: str) -> Optional[StockFundamentals]:
        """Get stock fundamentals from Yahoo Finance"""
        symbol = self._get_yahoo_symbol(ticker, exchange)
        
        try:
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(self.executor, yf.Ticker, symbol)
            
            # Get info which contains fundamentals
            info = None
            try:
                info = await loop.run_in_executor(self.executor, lambda: ticker_obj.info)
            except Exception as e:
                logger.warning(f"Could not fetch fundamentals info for {symbol}: {e}")
                return None
            
            if not info or not isinstance(info, dict):
                return None
            
            # Extract fundamentals
            market_cap = info.get("marketCap") or info.get("enterpriseValue")
            pe_ratio = info.get("trailingPE") or info.get("forwardPE")
            dividend_yield = info.get("dividendYield")
            dividend_amount = info.get("dividendRate")  # Annual dividend, divide by 4 for quarterly
            week_52_high = info.get("fiftyTwoWeekHigh")
            week_52_low = info.get("fiftyTwoWeekLow")
            beta = info.get("beta")
            eps = info.get("trailingEps") or info.get("forwardEps")
            book_value = info.get("bookValue")
            
            # Convert dividend yield from decimal to percentage if needed
            if dividend_yield and dividend_yield < 1:
                dividend_yield = dividend_yield * 100
            
            # Convert market cap to crores for Indian stocks (if in INR)
            if market_cap and exchange.upper() in ["NSE", "BSE"]:
                # Market cap is usually in rupees, convert to crores (divide by 10^7)
                market_cap_crores = market_cap / 10000000
            else:
                market_cap_crores = market_cap / 1000000 if market_cap else None  # Millions for US stocks
            
            logger.info(f"Fetched fundamentals for {symbol}: Market Cap={market_cap_crores}Cr, P/E={pe_ratio}, Div Yield={dividend_yield}%")
            
            return StockFundamentals(
                ticker=ticker.upper(),
                exchange=exchange.upper(),
                market_cap=round(market_cap_crores, 2) if market_cap_crores else None,
                pe_ratio=round(pe_ratio, 2) if pe_ratio else None,
                dividend_yield=round(dividend_yield, 2) if dividend_yield else None,
                dividend_amount=round((dividend_amount / 4), 2) if dividend_amount else None,  # Quarterly
                week_52_high=round(week_52_high, 2) if week_52_high else None,
                week_52_low=round(week_52_low, 2) if week_52_low else None,
                beta=round(beta, 2) if beta else None,
                eps=round(eps, 2) if eps else None,
                book_value=round(book_value, 2) if book_value else None,
                data_source="yahoo_finance"
            )
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {ticker} from Yahoo Finance: {e}", exc_info=True)
            return None

