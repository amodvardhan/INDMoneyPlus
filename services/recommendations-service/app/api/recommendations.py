"""Recommendations API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationSource, RecommendationType
from app.schemas.recommendation import (
    RecommendationRead,
    RecommendationCreate,
    RecommendationResponse,
    TopRecommendationsResponse,
)
import httpx
from app.core.config import settings
from app.core.cache import (
    get_cached_recommendations,
    set_cached_recommendations,
    invalidate_recommendations_cache
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/recommendations/top", response_model=TopRecommendationsResponse)
async def get_top_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations to return"),
    recommendation_type: Optional[str] = Query(None, description="Filter by type: buy, sell, hold"),
    force_refresh: bool = Query(False, description="Force regeneration of recommendations"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get top stock recommendations based on confidence, credibility, and recency.
    Dynamically generates recommendations using AI if none exist or they're stale.
    Uses Redis caching to avoid frequent regeneration.
    Returns buy and sell recommendations separately.
    """
    try:
        # Check Redis cache first (unless force refresh)
        if not force_refresh:
            cache_key = "top"
            cached_data = await get_cached_recommendations(
                cache_key, limit, recommendation_type
            )
            if cached_data:
                logger.info("Returning cached recommendations")
                return TopRecommendationsResponse(**cached_data)
        
        # Check if we have fresh recommendations in database (within refresh window)
        refresh_threshold = datetime.utcnow() - timedelta(hours=settings.recommendation_refresh_hours)
        
        if not force_refresh:
            # Check for recent recommendations in database
            recent_query = select(func.count(Recommendation.id)).where(
                Recommendation.is_active == "true",
                Recommendation.created_at > refresh_threshold
            )
            recent_count = await db.execute(recent_query)
            has_recent = recent_count.scalar() > 0
            
            if has_recent:
                # Use existing recommendations and cache them
                result = await _get_existing_recommendations(db, limit, recommendation_type)
                # Cache for the refresh period
                cache_ttl = settings.recommendation_refresh_hours * 3600
                await set_cached_recommendations(
                    "top",
                    result.model_dump(),
                    cache_ttl,
                    limit,
                    recommendation_type
                )
                return result
        
        # Generate new recommendations using AI agent
        await _generate_and_store_recommendations(db, limit)
        
        # Invalidate cache since we have new recommendations
        await invalidate_recommendations_cache("recommendations:top:*")
        
        # Get and cache the newly generated recommendations
        result = await _get_existing_recommendations(db, limit, recommendation_type)
        cache_ttl = settings.recommendation_refresh_hours * 3600
        await set_cached_recommendations(
            "top",
            result.model_dump(),
            cache_ttl,
            limit,
            recommendation_type
        )
        return result
        
    except Exception as e:
        logger.error(f"Failed to fetch recommendations: {e}")
        # Fallback to existing recommendations if generation fails
        try:
            return await _get_existing_recommendations(db, limit, recommendation_type)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch recommendations: {str(e)}"
            )


async def _get_existing_recommendations(
    db: AsyncSession,
    limit: int,
    recommendation_type: Optional[str]
) -> TopRecommendationsResponse:
    """Get existing recommendations from database"""
    query = select(Recommendation).where(
        Recommendation.is_active == "true",
        or_(
            Recommendation.expires_at.is_(None),
            Recommendation.expires_at > datetime.utcnow()
        )
    )
    
    if recommendation_type:
        try:
            rec_type = RecommendationType(recommendation_type.lower())
            query = query.where(Recommendation.recommendation_type == rec_type)
        except ValueError:
            pass
    
    # Get buy recommendations
    buy_query = query.where(
        Recommendation.recommendation_type.in_([
            RecommendationType.STRONG_BUY,
            RecommendationType.BUY
        ])
    ).order_by(
        Recommendation.confidence_score.desc(),
        Recommendation.created_at.desc()
    ).limit(limit)
    
    buy_result = await db.execute(buy_query)
    buy_recommendations = buy_result.scalars().all()
    
    # Get sell recommendations
    sell_query = query.where(
        Recommendation.recommendation_type.in_([
            RecommendationType.STRONG_SELL,
            RecommendationType.SELL
        ])
    ).order_by(
        Recommendation.confidence_score.desc(),
        Recommendation.created_at.desc()
    ).limit(limit)
    
    sell_result = await db.execute(sell_query)
    sell_recommendations = sell_result.scalars().all()
    
    # Load source relationships
    for rec in buy_recommendations + sell_recommendations:
        await db.refresh(rec, ["source"])
    
    return TopRecommendationsResponse(
        buy_recommendations=[RecommendationRead.model_validate(rec) for rec in buy_recommendations],
        sell_recommendations=[RecommendationRead.model_validate(rec) for rec in sell_recommendations],
        total_count=len(buy_recommendations) + len(sell_recommendations),
        last_updated=datetime.utcnow()
    )


async def _generate_and_store_recommendations(db: AsyncSession, limit: int):
    """Generate new recommendations using AI agent and store in database"""
    import httpx
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Call agent orchestrator to generate recommendations
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.agent_orchestrator_url}/api/v1/agents/recommendations",
                json={"limit": limit * 2}  # Get more to have good buy/sell split
            )
            response.raise_for_status()
            agent_response = response.json()
        
        recommendations_data = agent_response.get("recommendations", [])
        
        if not recommendations_data:
            logger.warning("Agent returned no recommendations, using fallback")
            # Don't return - let it try to use existing recommendations
            # This prevents clearing existing data when agent fails
            return
        
        # Deactivate old recommendations
        await db.execute(
            update(Recommendation).where(
                Recommendation.is_active == "true"
            ).values(is_active="false")
        )
        
        # Get or create AI source
        source_result = await db.execute(
            select(RecommendationSource).where(
                RecommendationSource.name == "AI Market Analyst"
            )
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            source = RecommendationSource(
                name="AI Market Analyst",
                source_type="ai_analysis",
                credibility_score=0.85,
                is_verified="true"
            )
            db.add(source)
            await db.flush()
        
        # Store new recommendations
        for rec_data in recommendations_data:
            # Map recommendation type
            rec_type_str = rec_data.get("recommendation_type", "HOLD").upper()
            try:
                rec_type = RecommendationType(rec_type_str.lower())
            except ValueError:
                rec_type = RecommendationType.HOLD
            
            new_rec = Recommendation(
                ticker=rec_data.get("ticker", "").upper(),
                exchange=rec_data.get("exchange", "NSE").upper(),
                recommendation_type=rec_type,
                target_price=float(rec_data.get("target_price", 0)),
                current_price=float(rec_data.get("current_price", 0)),
                reasoning=rec_data.get("reasoning", "AI-generated recommendation based on market analysis."),
                risk_level=rec_data.get("risk_level", "medium").lower(),
                confidence_score=float(rec_data.get("confidence_score", 0.5)),
                source_id=source.id,
                source_date=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=settings.recommendation_validity_days),
                is_active="true"
            )
            db.add(new_rec)
        
        await db.commit()
        logger.info(f"Stored {len(recommendations_data)} new recommendations")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to generate/store recommendations: {e}")
        raise


@router.get("/recommendations/{ticker}", response_model=List[RecommendationRead])
async def get_recommendations_for_ticker(
    ticker: str,
    exchange: Optional[str] = Query(None, description="Filter by exchange (NSE, BSE, etc.)"),
    db: AsyncSession = Depends(get_db)
):
    """Get all active recommendations for a specific ticker"""
    try:
        query = select(Recommendation).where(
            Recommendation.ticker == ticker.upper(),
            Recommendation.is_active == "true",
            or_(
                Recommendation.expires_at.is_(None),
                Recommendation.expires_at > datetime.utcnow()
            )
        )
        
        if exchange:
            query = query.where(Recommendation.exchange == exchange.upper())
        
        query = query.order_by(
            Recommendation.confidence_score.desc(),
            Recommendation.created_at.desc()
        )
        
        result = await db.execute(query)
        recommendations = result.scalars().all()
        
        # Load source relationships
        for rec in recommendations:
            await db.refresh(rec, ["source"])
        
        return [RecommendationRead.model_validate(rec) for rec in recommendations]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch recommendations: {str(e)}"
        )


@router.post("/recommendations", response_model=RecommendationRead, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    recommendation: RecommendationCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new recommendation.
    This endpoint can be used by internal systems or trusted sources to add recommendations.
    """
    try:
        # Get or create source
        source_result = await db.execute(
            select(RecommendationSource).where(
                RecommendationSource.name == recommendation.source_name
            )
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            source = RecommendationSource(
                name=recommendation.source_name,
                source_type=recommendation.source_type,
                credibility_score=0.7,  # Default for new sources
                is_verified="false"
            )
            db.add(source)
            await db.flush()
        
        # Create recommendation
        new_rec = Recommendation(
            ticker=recommendation.ticker.upper(),
            exchange=recommendation.exchange.upper(),
            recommendation_type=recommendation.recommendation_type,
            target_price=recommendation.target_price,
            current_price=recommendation.current_price,
            reasoning=recommendation.reasoning,
            risk_level=recommendation.risk_level,
            confidence_score=recommendation.confidence_score,
            source_id=source.id,
            source_url=recommendation.source_url,
            source_date=recommendation.source_date,
            expires_at=recommendation.expires_at or (
                datetime.utcnow() + timedelta(days=settings.recommendation_validity_days)
            ),
            is_active="true"
        )
        
        db.add(new_rec)
        await db.commit()
        await db.refresh(new_rec, ["source"])
        
        return RecommendationRead.model_validate(new_rec)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recommendation: {str(e)}"
        )


@router.get("/recommendations/{ticker}/detailed", response_model=RecommendationResponse)
async def get_detailed_recommendation(
    ticker: str,
    exchange: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed recommendation with market data and similar recommendations.
    Provides comprehensive view for a specific stock.
    """
    try:
        # Get recommendations
        query = select(Recommendation).where(
            Recommendation.ticker == ticker.upper(),
            Recommendation.is_active == "true"
        )
        
        if exchange:
            query = query.where(Recommendation.exchange == exchange.upper())
        
        query = query.order_by(
            Recommendation.confidence_score.desc()
        ).limit(1)
        
        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active recommendations found for {ticker}"
            )
        
        await db.refresh(recommendation, ["source"])
        
        # Fetch market data
        market_data = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                exchange_to_use = exchange or recommendation.exchange
                response = await client.get(
                    f"{settings.marketdata_service_url}/api/v1/price/{ticker}/latest",
                    params={"exchange": exchange_to_use}
                )
                if response.status_code == 200:
                    market_data = response.json()
        except Exception:
            pass  # Market data is optional
        
        # Get similar recommendations (same type)
        similar_query = select(Recommendation).where(
            Recommendation.recommendation_type == recommendation.recommendation_type,
            Recommendation.ticker != recommendation.ticker,
            Recommendation.is_active == "true"
        ).order_by(
            Recommendation.confidence_score.desc()
        ).limit(5)
        
        similar_result = await db.execute(similar_query)
        similar_recommendations = similar_result.scalars().all()
        for rec in similar_recommendations:
            await db.refresh(rec, ["source"])
        
        return RecommendationResponse(
            recommendation=RecommendationRead.model_validate(recommendation),
            market_data=market_data,
            similar_recommendations=[
                RecommendationRead.model_validate(rec) for rec in similar_recommendations
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch detailed recommendation: {str(e)}"
        )

