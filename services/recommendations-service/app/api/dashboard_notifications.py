"""Dashboard notifications API - Real-time notifications for users"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationType
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class DashboardNotification(BaseModel):
    """Dashboard notification model"""
    id: str
    type: str  # 'new_recommendation', 'price_alert', 'market_update'
    title: str
    message: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    recommendation_type: Optional[str] = None
    priority: str = 'normal'  # 'low', 'normal', 'high', 'urgent'
    created_at: datetime
    read: bool = False
    action_url: Optional[str] = None


@router.get("/notifications", response_model=List[DashboardNotification])
async def get_dashboard_notifications(
    user_id: int = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard notifications for a user
    Returns recent recommendations, price alerts, and market updates
    """
    try:
        notifications: List[DashboardNotification] = []
        
        # Get recent recommendations (last 24 hours) as notifications
        recent_threshold = datetime.utcnow() - timedelta(hours=24)
        
        query = select(Recommendation).where(
            and_(
                Recommendation.is_active == "true",
                Recommendation.created_at >= recent_threshold
            )
        ).order_by(Recommendation.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        recommendations = result.scalars().all()
        
        for rec in recommendations:
            rec_type_display = rec.recommendation_type.value.replace('_', ' ').title()
            # Ensure created_at is a datetime object
            created_at = rec.created_at
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.utcnow()
            
            notifications.append(DashboardNotification(
                id=f"rec_{rec.id}",
                type="new_recommendation",
                title=f"New {rec_type_display} Recommendation",
                message=f"{rec.ticker} ({rec.exchange}): {rec.reasoning[:100] if rec.reasoning else 'No reasoning provided'}...",
                ticker=rec.ticker,
                exchange=rec.exchange,
                recommendation_type=rec.recommendation_type.value,
                priority="high" if rec.recommendation_type in [RecommendationType.STRONG_BUY, RecommendationType.STRONG_SELL] else "normal",
                created_at=created_at,
                read=False,  # All notifications are unread by default
                action_url=f"/recommendations/{rec.ticker}?exchange={rec.exchange}"
            ))
        
        # Sort by created_at descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        
        # Limit results
        notifications = notifications[:limit]
        
        logger.info(f"Returned {len(notifications)} dashboard notifications for user {user_id}")
        return notifications
        
    except Exception as e:
        logger.error(f"Error fetching dashboard notifications: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notifications: {str(e)}"
        )


@router.get("/notifications/unread-count")
async def get_unread_count(
    user_id: int = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get count of unread notifications"""
    try:
        # Count recent recommendations (last 24 hours)
        recent_threshold = datetime.utcnow() - timedelta(hours=24)
        
        query = select(Recommendation).where(
            and_(
                Recommendation.is_active == "true",
                Recommendation.created_at >= recent_threshold
            )
        )
        
        result = await db.execute(query)
        count = len(result.scalars().all())
        
        return {
            "user_id": user_id,
            "unread_count": count,
            "last_checked": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching unread count: {e}", exc_info=True)
        return {
            "user_id": user_id,
            "unread_count": 0,
            "error": str(e)
        }
