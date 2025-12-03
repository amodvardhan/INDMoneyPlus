"""Tests for notification endpoints"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_create_notification(client: AsyncClient):
    """Test creating a notification"""
    with patch("app.core.workers.notification_worker.get_worker") as mock_worker:
        mock_worker_instance = AsyncMock()
        mock_worker.return_value = mock_worker_instance
        
        response = await client.post(
            "/api/v1/notifications/notify",
            json={
                "channel": "email",
                "recipient": "test@example.com",
                "payload": {
                    "subject": "Test Subject",
                    "body": "Test Body"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "notification_id" in data
        assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_get_notification_logs(client: AsyncClient, db_session):
    """Test getting notification logs"""
    from app.models.notification import Notification, NotificationLog
    
    # Create notification
    notification = Notification(
        recipient="test@example.com",
        channel="email",
        payload_json={"body": "Test"},
        status="sent"
    )
    db_session.add(notification)
    await db_session.commit()
    await db_session.refresh(notification)
    
    # Create log
    log = NotificationLog(
        notification_id=notification.id,
        channel="email",
        response_code=200,
        response_body="Sent successfully"
    )
    db_session.add(log)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/notifications/{notification.id}/logs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["response_code"] == 200


@pytest.mark.asyncio
async def test_notification_with_template(client: AsyncClient, db_session):
    """Test notification with template"""
    from app.models.notification import NotificationTemplate
    
    # Create template
    template = NotificationTemplate(
        name="test_template",
        channel="email",
        subject_template="Hello {{name}}",
        body_template="Welcome {{name}}! Your code is {{code}}."
    )
    db_session.add(template)
    await db_session.commit()
    
    with patch("app.core.workers.notification_worker.get_worker") as mock_worker:
        mock_worker_instance = AsyncMock()
        mock_worker.return_value = mock_worker_instance
        
        response = await client.post(
            "/api/v1/notifications/notify",
            json={
                "channel": "email",
                "recipient": "test@example.com",
                "template_name": "test_template",
                "payload": {
                    "name": "John",
                    "code": "12345"
                }
            }
        )
        
        assert response.status_code == 200

