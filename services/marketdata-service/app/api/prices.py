"""Price endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import Optional
from app.core.database import get_db
from app.core.adapters import MarketDataAdapter, InMemoryAdapter
from app.models.instrument import Instrument, PricePoint
from app.schemas.market_data import (
    PriceTimeseriesResponse,
    LatestPriceResponse,
    PricePointRead
)

router = APIRouter()

# Initialize adapter
_adapter: Optional[MarketDataAdapter] = None


def get_adapter() -> MarketDataAdapter:
    """Get market data adapter"""
    global _adapter
    if _adapter is None:
        _adapter = InMemoryAdapter()
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
    """Get the latest price for a ticker"""
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
    
    # Try to get latest from database first
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
    
    # Fallback to adapter
    latest = await adapter.get_latest_price(ticker, exchange)
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price data not available for {ticker} on {exchange}"
        )
    
    return latest

