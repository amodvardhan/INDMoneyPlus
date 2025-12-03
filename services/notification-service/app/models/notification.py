"""Database models for notification service"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    channel = Column(String, nullable=False, index=True)  # email, sms, push
    subject_template = Column(Text, nullable=True)  # For email
    body_template = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_notification_templates_name_channel', 'name', 'channel'),
    )


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String, nullable=False, index=True)  # email, phone, device_token
    channel = Column(String, nullable=False, index=True)  # email, sms, push
    template_name = Column(String, nullable=True, index=True)
    payload_json = Column(JSON, nullable=False)  # Template variables and metadata
    status = Column(String, nullable=False, default="pending", index=True)  # pending, sent, failed, retrying
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)  # For cron-like scheduling
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    logs = relationship("NotificationLog", back_populates="notification", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_notifications_status_next_attempt', 'status', 'next_attempt_at'),
        Index('ix_notifications_scheduled_at', 'scheduled_at'),
    )


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    event_type = Column(String, nullable=False, index=True)  # notification.sent, notification.failed, etc.
    secret = Column(String, nullable=True)  # For webhook signature verification
    active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('ix_webhook_subscriptions_event_type_active', 'event_type', 'active'),
    )


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String, nullable=False)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    notification = relationship("Notification", back_populates="logs")
    
    __table_args__ = (
        Index('ix_notification_logs_notification_created', 'notification_id', 'created_at'),
    )

