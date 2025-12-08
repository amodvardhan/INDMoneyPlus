"""Price endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import Optional
import logging
from app.core.database import get_db
from app.core.adapters import MarketDataAdapter, InMemoryAdapter
from app.core.cache import (
    get_cached_price,
    set_cached_price,
    invalidate_price_cache,
    flush_all_price_cache,
    get_cache_stats
)
from app.models.instrument import Instrument, PricePoint
from app.schemas.market_data import (
    PriceTimeseriesResponse,
    LatestPriceResponse,
    PricePointRead
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize adapter
_adapter: Optional[MarketDataAdapter] = None


def get_adapter() -> MarketDataAdapter:
    """Get market data adapter - NEVER uses InMemoryAdapter unless explicitly set for testing"""
    global _adapter
    if _adapter is None:
        from app.core.config import settings
        from app.core.adapters.yahoo_finance import YahooFinanceAdapter
        from app.core.adapters.tiingo import TiingoAdapter
        
        # Determine which adapter to use
        # IMPORTANT: InMemoryAdapter is ONLY for explicit testing - never auto-selected
        if settings.adapter_type == "in_memory":
            logger.warning("⚠️  WARNING: Using InMemoryAdapter (synthetic/fake data). This should ONLY be used for testing!")
            _adapter = InMemoryAdapter()
        elif settings.adapter_type == "tiingo" and settings.tiingo_api_key:
            _adapter = TiingoAdapter(api_key=settings.tiingo_api_key)
            logger.info("Using Tiingo adapter for real market data")
        elif settings.adapter_type == "yahoo_finance" or settings.adapter_type == "real" or settings.adapter_type == "auto":
            # Use Yahoo Finance for real data (default for auto if no Tiingo key)
            _adapter = YahooFinanceAdapter()
            logger.info("Using Yahoo Finance adapter for real market data")
        else:
            # Default to Yahoo Finance for real market data
            _adapter = YahooFinanceAdapter()
            logger.info("Using Yahoo Finance adapter for real market data (default)")
    return _adapter


@router.get("/prices/{ticker}", response_model=PriceTimeseriesResponse)
async def get_price_timeseries(
    ticker: str,
    exchange: str = Query(..., description="Exchange code (e.g., NSE, NASDAQ)"),
    from_date: datetime = Query(..., alias="from", description="Start date (ISO format)"),
    to_date: datetime = Query(..., alias="to", description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    adapter: MarketDataAdapter = Depends(get_adapter)
):
    """Get historical price timeseries for a ticker"""
    # Get instrument
    result = await db.execute(
        select(Instrument).where(
            Instrument.ticker == ticker.upper(),
            Instrument.exchange == exchange.upper()
        )
    )
    instrument = result.scalar_one_or_none()
    
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument {ticker} on {exchange} not found"
        )
    
    # Query price points from database
    result = await db.execute(
        select(PricePoint).where(
            and_(
                PricePoint.instrument_id == instrument.id,
                PricePoint.timestamp >= from_date,
                PricePoint.timestamp <= to_date
            )
        ).order_by(PricePoint.timestamp)
    )
    price_points = result.scalars().all()
    
    # If no data in database, fetch from adapter
    if not price_points:
        adapter_prices = await adapter.get_historical_prices(
            ticker, exchange, from_date, to_date
        )
        # Convert to PricePointRead with instrument_id
        price_points = [
            PricePointRead(
                id=0,
                instrument_id=instrument.id,
                timestamp=p.timestamp,
                open=p.open,
                high=p.high,
                low=p.low,
                close=p.close,
                volume=p.volume
            )
            for p in adapter_prices
        ]
    else:
        # Convert database models to schemas
        price_points = [
            PricePointRead(
                id=p.id,
                instrument_id=p.instrument_id,
                timestamp=p.timestamp,
                open=p.open,
                high=p.high,
                low=p.low,
                close=p.close,
                volume=p.volume
            )
            for p in price_points
        ]
    
    return PriceTimeseriesResponse(
        ticker=instrument.ticker,
        exchange=instrument.exchange,
        data=price_points,
        count=len(price_points)
    )


@router.get("/price/{ticker}/latest", response_model=LatestPriceResponse)
async def get_latest_price(
    ticker: str,
    exchange: str = Query(..., description="Exchange code (e.g., NSE, NASDAQ)"),
    force_refresh: bool = Query(False, description="Force refresh from adapter, bypassing cache"),
    db: AsyncSession = Depends(get_db),
    adapter: MarketDataAdapter = Depends(get_adapter)
):
    """
    Get the latest price for a ticker - ALWAYS fetches real-time prices from adapter.
    
    Uses Redis cache with 5-minute TTL for optimization, but validates that cached prices
    are from today and not older than 5 minutes. Set force_refresh=True to bypass cache.
    
    IMPORTANT: This endpoint NEVER returns stale database prices - it always fetches
    fresh from the market data adapter (Tiingo/Yahoo Finance).
    """
    cache_key = f"{ticker}:{exchange}"
    
    # Check cache first (unless force_refresh is True)
    # Cache is validated to ensure it's from today and not too old
    if not force_refresh:
        cached_data = await get_cached_price(ticker, exchange)
        if cached_data:
            # CRITICAL: Check if cached price is from today - if not, fetch fresh
            cached_timestamp_str = cached_data.get("timestamp")
            if cached_timestamp_str:
                try:
                    if isinstance(cached_timestamp_str, str):
                        cached_timestamp = datetime.fromisoformat(cached_timestamp_str.replace("Z", "+00:00"))
                    else:
                        cached_timestamp = cached_timestamp_str
                    
                    # Check if cached price is from today (same day in UTC)
                    now = datetime.utcnow()
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    # If cached price is not from today, force refresh
                    if cached_timestamp < today_start:
                        logger.info(
                            f"🔄 Cached price for {ticker} on {exchange} is from {cached_timestamp.date()}, "
                            f"not today ({now.date()}). Fetching fresh price..."
                        )
                        # Invalidate stale cache and fetch fresh
                        await invalidate_price_cache(ticker, exchange)
                        cached_data = None  # Force fresh fetch
                    else:
                        # Cached price is from today - check if it's too old (more than 2 minutes)
                        age_seconds = (now - cached_timestamp).total_seconds()
                        if age_seconds > 120:  # 2 minutes - very short for real-time prices
                            logger.info(
                                f"🔄 Cached price for {ticker} on {exchange} is {age_seconds:.0f}s old (>2min). "
                                f"Fetching fresh price..."
                            )
                            await invalidate_price_cache(ticker, exchange)
                            cached_data = None  # Force fresh fetch
                except Exception as e:
                    logger.warning(f"Error checking cache timestamp: {e}. Fetching fresh price.")
                    cached_data = None
            
            if cached_data:
                # Remove cache metadata before returning
                cached_data.pop("_cached_at", None)
                cached_data.pop("_cache_ttl", None)
                logger.info(
                    f"✅ Returning CACHED price for {ticker} on {exchange}: "
                    f"₹{cached_data.get('price')} from {cached_data.get('data_source', 'cache')} "
                    f"(cached at: {cached_timestamp_str})"
                )
                return LatestPriceResponse(**cached_data)
    
    # Cache miss or force_refresh - fetch from adapter
    logger.info(
        f"🔍 Fetching FRESH price for {ticker} on {exchange} "
        f"using adapter: {adapter.__class__.__name__} "
        f"(force_refresh={force_refresh})"
    )
    
    latest = await adapter.get_latest_price(ticker, exchange)
    
    if not latest:
        # Check if we're using InMemoryAdapter (fake data)
        if isinstance(adapter, InMemoryAdapter):
            logger.error(
                f"❌ ERROR: InMemoryAdapter (fake data) cannot fetch price for {ticker} on {exchange}. "
                f"Configure a real adapter (yahoo_finance or tiingo) to get actual market prices."
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    f"Price data not available: Using test adapter (fake data). "
                    f"Please configure a real market data adapter (yahoo_finance or tiingo) "
                    f"to fetch actual prices for {ticker} on {exchange}."
                )
            )
        
        # Real adapter failed - return error instead of stale cache
        logger.error(
            f"❌ ERROR: Failed to fetch real-time price for {ticker} on {exchange} from market data adapter. "
            f"Adapter: {adapter.__class__.__name__}. Returning error instead of stale/wrong data."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Unable to fetch real-time price data for {ticker} on {exchange}. "
                f"The market data adapter ({adapter.__class__.__name__}) returned no data. "
                f"Please check adapter configuration and ensure market data source is accessible."
            )
        )
    
    # Ensure data_source is set if adapter didn't set it
    if not latest.data_source:
        # Determine source from adapter type
        adapter_name = adapter.__class__.__name__.lower()
        if "yahoo" in adapter_name:
            latest.data_source = "yahoo_finance"
        elif "tiingo" in adapter_name:
            latest.data_source = "tiingo"
        elif "memory" in adapter_name:
            latest.data_source = "in_memory"
        else:
            latest.data_source = "unknown"
        logger.info(f"📝 Set data_source to '{latest.data_source}' for {ticker} on {exchange} (adapter: {adapter_name})")
    
    # Log the price source for debugging
    logger.info(
        f"✅ Fetched FRESH price for {ticker} on {exchange}: "
        f"₹{latest.price} from {latest.data_source} (timestamp: {latest.timestamp})"
    )
    
    # Cache the fresh price in Redis (2 minutes TTL for latest prices - very short for real-time)
    try:
        cache_data = latest.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if isinstance(cache_data.get("timestamp"), datetime):
            cache_data["timestamp"] = cache_data["timestamp"].isoformat()
        await set_cached_price(ticker, exchange, cache_data, ttl_seconds=120)  # 2 minutes only
    except Exception as e:
        logger.warning(f"Failed to cache price in Redis: {e}")
        # Continue even if caching fails
    
    # Get or create instrument
    result = await db.execute(
        select(Instrument).where(
            Instrument.ticker == ticker.upper(),
            Instrument.exchange == exchange.upper()
        )
    )
    instrument = result.scalar_one_or_none()
    
    if not instrument:
        instrument = Instrument(
            ticker=ticker.upper(),
            exchange=exchange.upper(),
            name=ticker.upper(),
            asset_class="EQUITY",
            timezone="Asia/Kolkata" if exchange.upper() in ["NSE", "BSE"] else "America/New_York"
        )
        db.add(instrument)
        await db.flush()
    
    # Store fresh price in database for historical tracking (not for latest price caching)
    try:
        price_point = PricePoint(
            instrument_id=instrument.id,
            timestamp=latest.timestamp,
            open=latest.open,
            high=latest.high,
            low=latest.low,
            close=latest.close,
            volume=latest.volume
        )
        db.add(price_point)
        await db.commit()
    except Exception as e:
        logger.warning(f"Failed to store price in database: {e}")
        await db.rollback()
    
    return latest


@router.post("/cache/flush")
async def flush_price_cache(
    ticker: Optional[str] = Query(None, description="Optional ticker to flush (if not provided, flushes all)"),
    exchange: Optional[str] = Query(None, description="Optional exchange to flush (required if ticker is provided)")
):
    """
    Flush price cache from Redis.
    
    - If ticker and exchange are provided: flush only that specific price cache
    - If neither provided: flush ALL price caches (use with caution!)
    """
    try:
        if ticker and exchange:
            await invalidate_price_cache(ticker, exchange)
            return {
                "status": "success",
                "message": f"Flushed cache for {ticker} on {exchange}",
                "ticker": ticker,
                "exchange": exchange
            }
        else:
            success = await flush_all_price_cache()
            if success:
                return {
                    "status": "success",
                    "message": "Flushed all price caches from Redis"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to flush cache"
                )
    except Exception as e:
        logger.error(f"Error flushing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error flushing cache: {str(e)}"
        )


@router.get("/cache/stats")
async def get_price_cache_stats():
    """Get Redis cache statistics for price data"""
    try:
        stats = await get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cache stats: {str(e)}"
        )

