"""Webhook subscription endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.notification import WebhookSubscription
from app.schemas.notification import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionRead,
)

router = APIRouter()


@router.post("/subscribe", response_model=WebhookSubscriptionRead)
async def subscribe_webhook(
    subscription: WebhookSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Subscribe to webhook events"""
    webhook_sub = WebhookSubscription(
        url=subscription.url,
        event_type=subscription.event_type,
        secret=subscription.secret,
        active=True
    )
    db.add(webhook_sub)
    await db.commit()
    await db.refresh(webhook_sub)
    
    return webhook_sub


@router.get("/subscriptions", response_model=list[WebhookSubscriptionRead])
async def list_webhook_subscriptions(
    db: AsyncSession = Depends(get_db)
):
    """List all webhook subscriptions"""
    result = await db.execute(select(WebhookSubscription))
    subscriptions = result.scalars().all()
    return subscriptions


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a webhook subscription"""
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook subscription {subscription_id} not found"
        )
    
    await db.delete(subscription)
    await db.commit()

