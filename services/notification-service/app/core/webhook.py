"""Webhook delivery"""
import httpx
import hmac
import hashlib
import json
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.notification import WebhookSubscription

logger = logging.getLogger(__name__)


async def deliver_webhook(
    db: AsyncSession,
    event_type: str,
    payload: Dict[str, Any]
):
    """Deliver webhook to all active subscribers for event type"""
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.event_type == event_type,
            WebhookSubscription.active == True
        )
    )
    subscriptions = result.scalars().all()
    
    for subscription in subscriptions:
        try:
            await _send_webhook(subscription, payload)
        except Exception as e:
            logger.error(f"Webhook delivery failed for {subscription.url}: {e}")


async def _send_webhook(subscription: WebhookSubscription, payload: Dict[str, Any]):
    """Send webhook to a single subscription"""
    payload_json = json.dumps(payload)
    headers = {"Content-Type": "application/json"}
    
    # Add signature if secret is configured
    if subscription.secret:
        signature = hmac.new(
            subscription.secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={signature}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            subscription.url,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        logger.info(f"Webhook delivered to {subscription.url}: {response.status_code}")

