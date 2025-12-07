"""Price endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import Optional
import logging
from app.core.database import get_db
from app.core.adapters import MarketDataAdapter, InMemoryAdapter
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
    """Get market data adapter"""
    global _adapter
    if _adapter is None:
        from app.core.config import settings
        from app.core.adapters.yahoo_finance import YahooFinanceAdapter
        from app.core.adapters.tiingo import TiingoAdapter
        
        # Prefer Tiingo if API key is available
        if settings.tiingo_api_key and (settings.adapter_type == "tiingo" or settings.adapter_type == "auto"):
            _adapter = TiingoAdapter(api_key=settings.tiingo_api_key)
            logger.info("Using Tiingo adapter for real market data")
        elif settings.adapter_type == "yahoo_finance" or settings.adapter_type == "real":
            _adapter = YahooFinanceAdapter()
            logger.info("Using Yahoo Finance adapter for real market data")
        else:
            _adapter = InMemoryAdapter()
            logger.info("Using InMemory adapter (synthetic data)")
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
    db: AsyncSession = Depends(get_db),
    adapter: MarketDataAdapter = Depends(get_adapter)
):
    """Get the latest price for a ticker - fetches real-time prices from adapter"""
    # Always fetch fresh price from adapter first (real-time data)
    latest = await adapter.get_latest_price(ticker, exchange)
    if not latest:
        # If adapter fails, try database cache
        result = await db.execute(
            select(Instrument).where(
                Instrument.ticker == ticker.upper(),
                Instrument.exchange == exchange.upper()
            )
        )
        instrument = result.scalar_one_or_none()
        if instrument:
            result = await db.execute(
                select(PricePoint).where(
                    PricePoint.instrument_id == instrument.id
                ).order_by(PricePoint.timestamp.desc()).limit(1)
            )
            latest_point = result.scalar_one_or_none()
            if latest_point:
                return LatestPriceResponse(
                    ticker=instrument.ticker,
                    exchange=instrument.exchange,
                    price=latest_point.close,
                    timestamp=latest_point.timestamp,
                    open=latest_point.open,
                    high=latest_point.high,
                    low=latest_point.low,
                    close=latest_point.close,
                    volume=latest_point.volume
                )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price data not available for {ticker} on {exchange}. Please ensure the ticker exists on {exchange}."
        )
    
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
    
    # Store fresh price in database for caching
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

