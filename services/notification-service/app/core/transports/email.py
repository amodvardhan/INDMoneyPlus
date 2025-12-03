"""Email transport implementations"""
import logging
from typing import Optional, Dict, Any
from app.core.transports.base import BaseTransport, TransportResult
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailTransport(BaseTransport):
    """Base email transport"""
    pass


class InMemoryEmailTransport(EmailTransport):
    """In-memory email transport for development/testing"""
    
    def __init__(self):
        self.sent_emails = []
        logger.info("InMemoryEmailTransport initialized")
    
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """Send email (stored in memory)"""
        from datetime import datetime
        email_data = {
            "recipient": recipient,
            "subject": subject,
            "body": body,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        self.sent_emails.append(email_data)
        
        logger.info(f"Email sent (in-memory) to {recipient}: {subject}")
        
        return TransportResult(
            success=True,
            response_code=200,
            response_body=f"Email queued for {recipient}"
        )
    
    def get_sent_emails(self):
        """Get all sent emails (for testing)"""
        return self.sent_emails


class SendGridEmailTransport(EmailTransport):
    """SendGrid email transport"""
    
    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.sendgrid_from_email or "noreply@example.com"
        if not self.api_key:
            logger.warning("SendGrid API key not configured")
    
    async def send(
        self,
        recipient: str,
        subject: Optional[str],
        body: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransportResult:
        """Send email via SendGrid"""
        if not self.api_key:
            return TransportResult(
                success=False,
                error_message="SendGrid API key not configured",
                response_code=500
            )
        
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.api_key)
            message = Mail(
                from_email=self.from_email,
                to_emails=recipient,
                subject=subject or "Notification",
                plain_text_content=body
            )
            
            response = sg.send(message)
            
            return TransportResult(
                success=200 <= response.status_code < 300,
                response_code=response.status_code,
                response_body=str(response.body)
            )
        except ImportError:
            logger.error("SendGrid library not installed")
            return TransportResult(
                success=False,
                error_message="SendGrid library not installed",
                response_code=500
            )
        except Exception as e:
            logger.error(f"SendGrid send error: {e}")
            return TransportResult(
                success=False,
                error_message=str(e),
                response_code=500
            )

