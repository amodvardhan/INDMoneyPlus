"""Transport factory"""
import logging
from app.core.config import settings
from app.core.transports.email import InMemoryEmailTransport, SendGridEmailTransport
from app.core.transports.sms import InMemorySMSTransport, TwilioSMSTransport
from app.core.transports.push import InMemoryPushTransport, FirebasePushTransport
from app.core.transports.base import BaseTransport

logger = logging.getLogger(__name__)

# Global transport instances
_email_transport: BaseTransport = None
_sms_transport: BaseTransport = None
_push_transport: BaseTransport = None


def get_email_transport() -> BaseTransport:
    """Get email transport instance"""
    global _email_transport
    if _email_transport is None:
        if settings.email_transport_type == "sendgrid":
            _email_transport = SendGridEmailTransport()
        else:
            _email_transport = InMemoryEmailTransport()
    return _email_transport


def get_sms_transport() -> BaseTransport:
    """Get SMS transport instance"""
    global _sms_transport
    if _sms_transport is None:
        if settings.sms_transport_type == "twilio":
            _sms_transport = TwilioSMSTransport()
        else:
            _sms_transport = InMemorySMSTransport()
    return _sms_transport


def get_push_transport() -> BaseTransport:
    """Get push notification transport instance"""
    global _push_transport
    if _push_transport is None:
        if settings.push_transport_type == "firebase":
            _push_transport = FirebasePushTransport()
        else:
            _push_transport = InMemoryPushTransport()
    return _push_transport


def get_transport(channel: str) -> BaseTransport:
    """Get transport for channel"""
    if channel == "email":
        return get_email_transport()
    elif channel == "sms":
        return get_sms_transport()
    elif channel == "push":
        return get_push_transport()
    else:
        raise ValueError(f"Unknown channel: {channel}")

