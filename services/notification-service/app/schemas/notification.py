"""Pydantic schemas for notification service"""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, Dict, Any


class NotificationTemplateBase(BaseModel):
    name: str
    channel: str  # email, sms, push
    subject_template: Optional[str] = None
    body_template: str


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateRead(NotificationTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationRequest(BaseModel):
    channel: str = Field(..., description="Channel: email, sms, or push")
    recipient: str = Field(..., description="Recipient: email address, phone number, or device token")
    template_name: Optional[str] = Field(None, description="Template name to use")
    payload: Dict[str, Any] = Field(..., description="Template variables and metadata")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule notification for future time")


class NotificationResponse(BaseModel):
    notification_id: int
    status: str
    message: str


class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(..., description="Webhook URL to call")
    event_type: str = Field(..., description="Event type to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for webhook signature verification")


class WebhookSubscriptionRead(WebhookSubscriptionCreate):
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class NotificationLogRead(BaseModel):
    id: int
    notification_id: int
    channel: str
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventIngestRequest(BaseModel):
    event_type: str = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")

