"""Pydantic schemas for market data"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class InstrumentBase(BaseModel):
    isin: Optional[str] = None
    ticker: str
    exchange: str
    name: str
    asset_class: str
    timezone: str = "UTC"


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentRead(InstrumentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PricePointBase(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = 0


class PricePointCreate(PricePointBase):
    instrument_id: int


class PricePointRead(PricePointBase):
    id: int
    instrument_id: int
    
    class Config:
        from_attributes = True


class CorporateActionBase(BaseModel):
    instrument_id: int
    type: str  # DIVIDEND, SPLIT, BONUS, MERGER, etc.
    effective_date: datetime
    payload_json: Optional[Dict[str, Any]] = None


class CorporateActionCreate(CorporateActionBase):
    pass


class CorporateActionRead(CorporateActionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PriceTimeseriesRequest(BaseModel):
    from_date: datetime = Field(..., alias="from")
    to_date: datetime = Field(..., alias="to")
    
    class Config:
        populate_by_name = True


class PriceTimeseriesResponse(BaseModel):
    ticker: str
    exchange: str
    data: List[PricePointRead]
    count: int


class LatestPriceResponse(BaseModel):
    ticker: str
    exchange: str
    price: float
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None
    data_source: Optional[str] = None  # e.g., "yahoo_finance", "tiingo", "in_memory"
    change_percent: Optional[float] = None  # Price change percentage


class StockFundamentals(BaseModel):
    """Stock fundamental data like market cap, P/E ratio, etc."""
    ticker: str
    exchange: str
    market_cap: Optional[float] = None  # Market capitalization
    pe_ratio: Optional[float] = None  # Price-to-Earnings ratio
    dividend_yield: Optional[float] = None  # Dividend yield percentage
    dividend_amount: Optional[float] = None  # Quarterly dividend amount
    week_52_high: Optional[float] = None  # 52-week high
    week_52_low: Optional[float] = None  # 52-week low
    beta: Optional[float] = None  # Beta (volatility measure)
    eps: Optional[float] = None  # Earnings per share
    book_value: Optional[float] = None  # Book value per share
    data_source: Optional[str] = None


class MarketCondition(str, Enum):
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    NEUTRAL = "neutral"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"


class IndexHealth(BaseModel):
    name: str
    ticker: str
    exchange: str
    current_value: float
    change: float
    change_percent: float
    volume: Optional[int] = None
    trend: str  # strong_bullish, bullish, neutral, bearish, strong_bearish


class MarketHealthResponse(BaseModel):
    condition: MarketCondition
    health_score: float = Field(..., description="Health score from 0-100")
    sentiment: str
    overall_change_percent: float
    volatility: str  # Low, Medium, High
    indices: List[IndexHealth]
    last_updated: datetime
    recommendation: str  # Buy, Hold, Caution

