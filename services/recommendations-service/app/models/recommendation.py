"""Recommendation models"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class RecommendationType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


class RecommendationSource(Base):
    """Sources of recommendations (research firms, analysts, news, etc.)"""
    __tablename__ = "recommendation_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)  # e.g., "Morgan Stanley", "Economic Times"
    source_type = Column(String, nullable=False)  # "research_firm", "news", "analyst", "blog"
    credibility_score = Column(Float, default=0.5)  # 0-1 scale
    is_verified = Column(String, default="false")  # Whether source is verified/legitimate
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recommendations = relationship("Recommendation", back_populates="source")


class Recommendation(Base):
    """Stock recommendations with sources and reasoning"""
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    exchange = Column(String, nullable=False, index=True)  # NSE, BSE, etc.
    recommendation_type = Column(SQLEnum(RecommendationType), nullable=False, index=True)
    target_price = Column(Float, nullable=True)  # Target price if available
    current_price = Column(Float, nullable=True)  # Price at time of recommendation
    reasoning = Column(Text, nullable=False)  # Detailed reasoning
    risk_level = Column(String, nullable=False, default="medium")  # low, medium, high
    confidence_score = Column(Float, default=0.5)  # 0-1 scale
    
    # Source information
    source_id = Column(Integer, ForeignKey("recommendation_sources.id"), nullable=False, index=True)
    source_url = Column(String, nullable=True)  # Link to original source
    source_date = Column(DateTime, nullable=False)  # When recommendation was made by source
    
    # Metadata
    is_active = Column(String, default="true")  # Whether recommendation is still valid
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    source = relationship("RecommendationSource", back_populates="recommendations")
    
    __table_args__ = (
        Index('ix_recommendations_ticker_exchange', 'ticker', 'exchange'),
        Index('ix_recommendations_active_expires', 'is_active', 'expires_at'),
    )

