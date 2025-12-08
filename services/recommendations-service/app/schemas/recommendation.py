"""Recommendation schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.models.recommendation import RecommendationType


class RecommendationSourceRead(BaseModel):
    id: int
    name: str
    source_type: str
    credibility_score: float
    is_verified: str
    
    class Config:
        from_attributes = True


class RecommendationRead(BaseModel):
    id: int
    ticker: str
    exchange: str
    recommendation_type: RecommendationType
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    reasoning: str
    risk_level: str
    confidence_score: float
    source: RecommendationSourceRead
    source_url: Optional[str] = None
    source_date: datetime
    is_active: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    # Price metadata
    price_is_stale: Optional[bool] = False  # True if using stored price instead of fresh
    price_age_hours: Optional[float] = None  # Age of price in hours
    price_last_updated: Optional[datetime] = None  # When price was last updated
    price_source: Optional[str] = None  # Source of price data: "yahoo_finance", "tiingo", "stored", etc.
    
    class Config:
        from_attributes = True


class RecommendationCreate(BaseModel):
    ticker: str
    exchange: str
    recommendation_type: RecommendationType
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    reasoning: str
    risk_level: str = "medium"
    confidence_score: float = Field(0.5, ge=0.0, le=1.0)
    source_name: str
    source_type: str = "research_firm"
    source_url: Optional[str] = None
    source_date: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class RecommendationResponse(BaseModel):
    recommendation: RecommendationRead
    market_data: Optional[dict] = None  # Current price, change, etc.
    similar_recommendations: Optional[List[RecommendationRead]] = None


class TopRecommendationsResponse(BaseModel):
    buy_recommendations: List[RecommendationRead]
    sell_recommendations: List[RecommendationRead]
    total_count: int
    last_updated: datetime

