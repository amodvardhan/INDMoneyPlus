"""Background worker for processing notification queue"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.notification import Notification, NotificationLog, NotificationTemplate
from app.core.transports.factory import get_transport
from app.core.template_engine import render_template

logger = logging.getLogger(__name__)


class NotificationWorker:
    """Background worker to process notification queue"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(settings.redis_url)
        logger.info("NotificationWorker initialized")
    
    async def start(self):
        """Start the worker"""
        if self.running:
            logger.warning("Worker already running")
            return
        
        await self.initialize()
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("NotificationWorker started")
    
    async def stop(self):
        """Stop the worker"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.redis_client:
            await self.redis_client.close()
        logger.info("NotificationWorker stopped")
    
    async def enqueue_notification(self, notification_id: int):
        """Enqueue notification for processing"""
        if not self.redis_client:
            await self.initialize()
        
        await self.redis_client.lpush(
            settings.redis_queue_key,
            json.dumps({"notification_id": notification_id})
        )
        logger.debug(f"Enqueued notification {notification_id}")
    
    async def _run_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                await self._process_batch()
                await asyncio.sleep(settings.worker_poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(settings.worker_poll_interval)
    
    async def _process_batch(self):
        """Process a batch of notifications"""
        if not self.redis_client:
            return
        
        # Get notifications ready for processing
        async with AsyncSessionLocal() as db:
            now = datetime.utcnow()
            result = await db.execute(
                select(Notification).where(
                    Notification.status.in_(["pending", "retrying"]),
                    (Notification.next_attempt_at.is_(None)) | (Notification.next_attempt_at <= now),
                    (Notification.scheduled_at.is_(None)) | (Notification.scheduled_at <= now)
                ).limit(settings.worker_batch_size)
            )
            notifications = result.scalars().all()
            
            for notification in notifications:
                await self._process_notification(notification, db)
                await db.commit()
    
    async def _process_notification(self, notification: Notification, db: AsyncSession):
        """Process a single notification"""
        try:
            # Get template if specified
            subject = None
            body = notification.payload_json.get("body", "")
            
            if notification.template_name:
                result = await db.execute(
                    select(NotificationTemplate).where(
                        NotificationTemplate.name == notification.template_name,
                        NotificationTemplate.channel == notification.channel
                    )
                )
                template = result.scalar_one_or_none()
                
                if template:
                    subject = render_template(template.subject_template or "", notification.payload_json)
                    body = render_template(template.body_template, notification.payload_json)
                else:
                    logger.warning(f"Template {notification.template_name} not found")
            
            # Get transport and send
            transport = get_transport(notification.channel)
            result = await transport.send(
                recipient=notification.recipient,
                subject=subject,
                body=body,
                metadata=notification.payload_json
            )
            
            # Log the result
            log_entry = NotificationLog(
                notification_id=notification.id,
                channel=notification.channel,
                response_code=result.response_code,
                response_body=result.response_body
            )
            db.add(log_entry)
            
            # Update notification status
            if result.success:
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                notification.next_attempt_at = None
                logger.info(f"Notification {notification.id} sent successfully")
            else:
                # Retry logic
                notification.attempts += 1
                if notification.attempts >= settings.max_retry_attempts:
                    notification.status = "failed"
                    notification.next_attempt_at = None
                    logger.error(f"Notification {notification.id} failed after {notification.attempts} attempts")
                else:
                    # Exponential backoff
                    backoff_seconds = settings.retry_backoff_base ** notification.attempts
                    notification.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                    notification.status = "retrying"
                    logger.warning(f"Notification {notification.id} will retry in {backoff_seconds}s")
        
        except Exception as e:
            logger.error(f"Error processing notification {notification.id}: {e}")
            notification.attempts += 1
            if notification.attempts >= settings.max_retry_attempts:
                notification.status = "failed"
            else:
                backoff_seconds = settings.retry_backoff_base ** notification.attempts
                notification.next_attempt_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                notification.status = "retrying"


# Global worker instance
_worker: Optional[NotificationWorker] = None


async def get_worker() -> NotificationWorker:
    """Get or create worker instance"""
    global _worker
    if _worker is None:
        _worker = NotificationWorker()
        await _worker.initialize()
    return _worker

