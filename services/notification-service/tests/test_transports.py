"""Tests for transport implementations"""
import pytest
from app.core.transports.email import InMemoryEmailTransport
from app.core.transports.sms import InMemorySMSTransport
from app.core.transports.push import InMemoryPushTransport


@pytest.mark.asyncio
async def test_in_memory_email_transport():
    """Test in-memory email transport"""
    transport = InMemoryEmailTransport()
    result = await transport.send(
        recipient="test@example.com",
        subject="Test Subject",
        body="Test Body"
    )
    
    assert result.success is True
    assert result.response_code == 200
    assert len(transport.get_sent_emails()) == 1
    assert transport.get_sent_emails()[0]["recipient"] == "test@example.com"


@pytest.mark.asyncio
async def test_in_memory_sms_transport():
    """Test in-memory SMS transport"""
    transport = InMemorySMSTransport()
    result = await transport.send(
        recipient="+1234567890",
        subject=None,
        body="Test SMS"
    )
    
    assert result.success is True
    assert len(transport.get_sent_sms()) == 1
    assert transport.get_sent_sms()[0]["recipient"] == "+1234567890"


@pytest.mark.asyncio
async def test_in_memory_push_transport():
    """Test in-memory push transport"""
    transport = InMemoryPushTransport()
    result = await transport.send(
        recipient="device_token_123",
        subject="Test Title",
        body="Test Push Notification"
    )
    
    assert result.success is True
    assert len(transport.get_sent_push()) == 1
    assert transport.get_sent_push()[0]["recipient"] == "device_token_123"

