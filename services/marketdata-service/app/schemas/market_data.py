"""Pydantic schemas for market data"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


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

