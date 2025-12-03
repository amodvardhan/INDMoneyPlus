"""Notification endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.notification import Notification, NotificationLog
from app.schemas.notification import (
    NotificationRequest,
    NotificationResponse,
    NotificationLogRead,
)
from app.core.workers.notification_worker import get_worker
from app.core.webhook import deliver_webhook

router = APIRouter()


@router.post("/notify", response_model=NotificationResponse)
async def create_notification(
    request: NotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Enqueue a notification for sending"""
    # Validate channel
    if request.channel not in ["email", "sms", "push"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid channel: {request.channel}. Must be email, sms, or push"
        )
    
    # Create notification record
    notification = Notification(
        recipient=request.recipient,
        channel=request.channel,
        template_name=request.template_name,
        payload_json=request.payload,
        status="pending",
        scheduled_at=request.scheduled_at
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    
    # Enqueue for processing
    worker = await get_worker()
    await worker.enqueue_notification(notification.id)
    
    # Deliver webhook for notification.created event
    await deliver_webhook(
        db,
        "notification.created",
        {
            "notification_id": notification.id,
            "channel": notification.channel,
            "recipient": notification.recipient
        }
    )
    
    return NotificationResponse(
        notification_id=notification.id,
        status=notification.status,
        message="Notification queued for processing"
    )


@router.get("/{notification_id}/logs", response_model=list[NotificationLogRead])
async def get_notification_logs(
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get logs for a notification"""
    # Verify notification exists
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found"
        )
    
    # Get logs
    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.notification_id == notification_id)
        .order_by(NotificationLog.created_at)
    )
    logs = result.scalars().all()
    
    return logs

