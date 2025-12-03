"""SMS transport implementations"""
import logging
from typing import Optional, Dict, Any
from app.core.transports.base import BaseTransport, TransportResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSTransport(BaseTransport):
    """Base SMS transport"""
    pass


class InMemorySMSTransport(SMSTransport):
    """In-memory SMS transport for development/testing"""
    
    def __init__(self):
        self.sent_sms = []
        logger.info("InMemorySMSTransport initialized")
    
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """Send SMS (stored in memory)"""
        from datetime import datetime
        sms_data = {
            "recipient": recipient,
            "body": body,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        self.sent_sms.append(sms_data)
        
        logger.info(f"SMS sent (in-memory) to {recipient}")
        
        return TransportResult(
            success=True,
            response_code=200,
            response_body=f"SMS queued for {recipient}"
        )
    
    def get_sent_sms(self):
        """Get all sent SMS (for testing)"""
        return self.sent_sms


class TwilioSMSTransport(SMSTransport):
    """Twilio SMS transport"""
    
    def __init__(self):
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_from_number
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not configured")
    
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """Send SMS via Twilio"""
        if not self.account_sid or not self.auth_token:
            return TransportResult(
                success=False,
                error_message="Twilio credentials not configured",
                response_code=500
            )
        
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            message = client.messages.create(
                body=body,
                from_=self.from_number,
                to=recipient
            )
            
            return TransportResult(
                success=True,
                response_code=200,
                response_body=f"Message SID: {message.sid}"
            )
        except ImportError:
            logger.error("Twilio library not installed")
            return TransportResult(
                success=False,
                error_message="Twilio library not installed",
                response_code=500
            )
        except Exception as e:
            logger.error(f"Twilio send error: {e}")
            return TransportResult(
                success=False,
                error_message=str(e),
                response_code=500
            )

