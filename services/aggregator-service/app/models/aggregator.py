"""Database models for aggregator service"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    broker_name = Column(String, nullable=False, index=True)  # e.g., "Zerodha", "ICICI", "HDFC"
    external_account_id = Column(String, nullable=False)  # Account ID from broker
    account_metadata = Column(JSON, nullable=True)  # Additional broker-specific data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    raw_statements = relationship("RawStatement", back_populates="account", cascade="all, delete-orphan")
    normalized_holdings = relationship("NormalizedHolding", back_populates="account", cascade="all, delete-orphan")
    reconciliation_exceptions = relationship("ReconciliationException", back_populates="account")
    
    __table_args__ = (
        Index('ix_broker_accounts_user_broker', 'user_id', 'broker_name'),
        Index('ix_broker_accounts_external_id', 'external_account_id'),
    )


class RawStatement(Base):
    __tablename__ = "raw_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    content_type = Column(String, nullable=False)  # "csv", "email", "api", "pdf"
    payload_json = Column(JSON, nullable=False)  # Raw statement data
    statement_hash = Column(String, nullable=False, unique=True, index=True)  # For idempotency
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    account = relationship("BrokerAccount", back_populates="raw_statements")


class NormalizedHolding(Base):
    __tablename__ = "normalized_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(Integer, nullable=True, index=True)  # Reference to marketdata service instrument
    isin = Column(String, nullable=True, index=True)  # ISIN for instrument matching
    ticker = Column(String, nullable=True, index=True)  # Ticker for instrument matching
    exchange = Column(String, nullable=True)  # Exchange code
    qty = Column(Float, nullable=False)  # Quantity/units
    avg_price = Column(Float, nullable=True)  # Average purchase price
    valuation = Column(Float, nullable=True)  # Current valuation
    source = Column(String, nullable=False)  # "csv", "email", "api"
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    account = relationship("BrokerAccount", back_populates="normalized_holdings")
    
    __table_args__ = (
        Index('ix_normalized_holdings_account_instrument', 'account_id', 'instrument_id'),
        Index('ix_normalized_holdings_account_updated', 'account_id', 'updated_at'),
    )


class ReconciliationException(Base):
    __tablename__ = "reconciliation_exceptions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    payload_json = Column(JSON, nullable=True)  # Exception context
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    account = relationship("BrokerAccount", back_populates="reconciliation_exceptions")


class InstrumentMapping(Base):
    """Mapping table for ISIN/Ticker normalization"""
    __tablename__ = "instrument_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    isin = Column(String, nullable=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False, index=True)
    instrument_id = Column(Integer, nullable=True)  # Reference to marketdata service
    broker_variant = Column(String, nullable=True)  # Variant name from broker
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_instrument_mappings_ticker_exchange', 'ticker', 'exchange'),
        Index('ix_instrument_mappings_isin', 'isin'),
    )

