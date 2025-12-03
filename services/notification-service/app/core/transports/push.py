"""Push notification transport implementations"""
import logging
from typing import Optional, Dict, Any
from app.core.transports.base import BaseTransport, TransportResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class PushTransport(BaseTransport):
    """Base push notification transport"""
    pass


class InMemoryPushTransport(PushTransport):
    """In-memory push transport for development/testing"""
    
    def __init__(self):
        self.sent_push = []
        logger.info("InMemoryPushTransport initialized")
    
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """Send push notification (stored in memory)"""
        from datetime import datetime
        push_data = {
            "recipient": recipient,  # device_token
            "title": subject,
            "body": body,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        self.sent_push.append(push_data)
        
        logger.info(f"Push notification sent (in-memory) to device {recipient[:20]}...")
        
        return TransportResult(
            success=True,
            response_code=200,
            response_body=f"Push notification queued for device"
        )
    
    def get_sent_push(self):
        """Get all sent push notifications (for testing)"""
        return self.sent_push


class FirebasePushTransport(PushTransport):
    """Firebase Cloud Messaging push transport"""
    
    def __init__(self):
        self.credentials_path = settings.firebase_credentials_path
        if not self.credentials_path:
            logger.warning("Firebase credentials path not configured")
    
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """Send push notification via Firebase"""
        if not self.credentials_path:
            return TransportResult(
                success=False,
                error_message="Firebase credentials path not configured",
                response_code=500
            )
        
        try:
            import firebase_admin
            from firebase_admin import credentials, messaging
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=subject or "Notification",
                    body=body
                ),
                token=recipient,
                data=metadata or {}
            )
            
            response = messaging.send(message)
            
            return TransportResult(
                success=True,
                response_code=200,
                response_body=f"Message ID: {response}"
            )
        except ImportError:
            logger.error("Firebase Admin library not installed")
            return TransportResult(
                success=False,
                error_message="Firebase Admin library not installed",
                response_code=500
            )
        except Exception as e:
            logger.error(f"Firebase send error: {e}")
            return TransportResult(
                success=False,
                error_message=str(e),
                response_code=500
            )

