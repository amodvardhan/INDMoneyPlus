"""Instrument endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from app.core.database import get_db
from app.core.adapters import MarketDataAdapter, InMemoryAdapter
from app.models.instrument import Instrument
from app.schemas.market_data import InstrumentRead, InstrumentCreate

router = APIRouter()

_adapter: Optional[MarketDataAdapter] = None


def get_adapter() -> MarketDataAdapter:
    """Get market data adapter"""
    global _adapter
    if _adapter is None:
        _adapter = InMemoryAdapter()
    return _adapter


@router.get("", response_model=List[InstrumentRead])
async def list_instruments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by ticker or name"),
    exchange: Optional[str] = Query(None, description="Filter by exchange"),
    asset_class: Optional[str] = Query(None, description="Filter by asset class"),
    db: AsyncSession = Depends(get_db)
):
    """List all instruments with optional filtering"""
    query = select(Instrument)
    
    if search:
        query = query.where(
            or_(
                Instrument.ticker.ilike(f"%{search}%"),
                Instrument.name.ilike(f"%{search}%")
            )
        )
    
    if exchange:
        query = query.where(Instrument.exchange == exchange.upper())
    
    if asset_class:
        query = query.where(Instrument.asset_class == asset_class.upper())
    
    query = query.offset(skip).limit(limit).order_by(Instrument.ticker)
    
    result = await db.execute(query)
    instruments = result.scalars().all()
    
    return instruments


@router.get("/{ticker}", response_model=InstrumentRead)
async def get_instrument(
    ticker: str,
    exchange: str = Query(..., description="Exchange code (e.g., NSE, NASDAQ)"),
    db: AsyncSession = Depends(get_db)
):
    """Get instrument by ticker and exchange"""
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
    
    return instrument


@router.post("", response_model=InstrumentRead, status_code=status.HTTP_201_CREATED)
async def create_instrument(
    instrument_data: InstrumentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new instrument"""
    # Check if instrument already exists
    result = await db.execute(
        select(Instrument).where(
            Instrument.ticker == instrument_data.ticker.upper(),
            Instrument.exchange == instrument_data.exchange.upper()
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Instrument {instrument_data.ticker} on {instrument_data.exchange} already exists"
        )
    
    instrument = Instrument(
        isin=instrument_data.isin,
        ticker=instrument_data.ticker.upper(),
        exchange=instrument_data.exchange.upper(),
        name=instrument_data.name,
        asset_class=instrument_data.asset_class.upper(),
        timezone=instrument_data.timezone
    )
    
    db.add(instrument)
    await db.commit()
    await db.refresh(instrument)
    
    return instrument

