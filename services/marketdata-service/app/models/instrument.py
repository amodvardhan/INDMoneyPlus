"""Market data models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Instrument(Base):
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, index=True)
    isin = Column(String, unique=True, index=True, nullable=True)  # Optional for some instruments
    ticker = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False, index=True)  # e.g., "NSE", "BSE", "NYSE", "NASDAQ"
    name = Column(String, nullable=False)
    asset_class = Column(String, nullable=False)  # e.g., "EQUITY", "BOND", "ETF", "MUTUAL_FUND"
    timezone = Column(String, nullable=False, default="UTC")  # e.g., "Asia/Kolkata", "America/New_York"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    price_points = relationship("PricePoint", back_populates="instrument", cascade="all, delete-orphan")
    corporate_actions = relationship("CorporateAction", back_populates="instrument", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_instruments_ticker_exchange', 'ticker', 'exchange', unique=True),
    )


class PricePoint(Base):
    __tablename__ = "price_points"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=True, default=0)
    
    # Relationships
    instrument = relationship("Instrument", back_populates="price_points")
    
    __table_args__ = (
        Index('ix_price_points_instrument_timestamp', 'instrument_id', 'timestamp'),
    )


class CorporateAction(Base):
    __tablename__ = "corporate_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False, index=True)  # e.g., "DIVIDEND", "SPLIT", "BONUS", "MERGER"
    effective_date = Column(DateTime, nullable=False, index=True)
    payload_json = Column(JSON, nullable=True)  # Flexible JSON for action-specific data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    instrument = relationship("Instrument", back_populates="corporate_actions")
    
    __table_args__ = (
        Index('ix_corporate_actions_instrument_effective_date', 'instrument_id', 'effective_date'),
    )

