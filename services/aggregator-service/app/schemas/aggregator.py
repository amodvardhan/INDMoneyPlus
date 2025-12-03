"""Pydantic schemas for aggregator service"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class BrokerAccountBase(BaseModel):
    broker_name: str
    external_account_id: str
    metadata: Optional[Dict[str, Any]] = None


class BrokerAccountCreate(BrokerAccountBase):
    user_id: int


class BrokerAccountRead(BrokerAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RawStatementCreate(BaseModel):
    account_id: int
    content_type: str
    payload_json: Dict[str, Any]
    statement_hash: str


class RawStatementRead(BaseModel):
    id: int
    account_id: int
    content_type: str
    payload_json: Dict[str, Any]
    statement_hash: str
    ingested_at: datetime
    
    class Config:
        from_attributes = True


class NormalizedHoldingBase(BaseModel):
    isin: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    qty: float
    avg_price: Optional[float] = None
    valuation: Optional[float] = None
    source: str


class NormalizedHoldingRead(NormalizedHoldingBase):
    id: int
    account_id: int
    instrument_id: Optional[int] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReconciliationExceptionRead(BaseModel):
    id: int
    account_id: int
    message: str
    payload_json: Optional[Dict[str, Any]] = None
    resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ConsolidatedHolding(BaseModel):
    instrument_id: Optional[int] = None
    isin: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    total_qty: float
    avg_price: Optional[float] = None
    total_valuation: Optional[float] = None
    accounts: List[Dict[str, Any]]  # List of accounts holding this instrument


class HoldingsResponse(BaseModel):
    user_id: int
    holdings: List[ConsolidatedHolding]
    total_valuation: Optional[float] = None
    last_updated: datetime


class CSVUploadResponse(BaseModel):
    statement_id: int
    account_id: int
    records_processed: int
    holdings_created: int
    message: str


class EmailIngestRequest(BaseModel):
    account_id: int
    email_subject: str
    payload_json: Dict[str, Any]
    statement_hash: Optional[str] = None


class BrokerAPIIngestRequest(BaseModel):
    account_id: int
    broker_name: str
    holdings: List[Dict[str, Any]]
    statement_hash: Optional[str] = None

