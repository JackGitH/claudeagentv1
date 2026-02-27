"""Message schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.message import MessageStatus, SentimentType


class MessageBase(BaseModel):
    """Base message schema."""
    title: Optional[str] = None
    content: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None


class MessageCreate(MessageBase):
    """Message creation schema."""
    subscription_id: int
    external_id: Optional[str] = None


class MessageResponse(MessageBase):
    """Message response schema."""
    id: int
    subscription_id: int
    external_id: Optional[str] = None
    status: MessageStatus
    summary: Optional[str] = None
    category: Optional[str] = None
    sentiment: Optional[SentimentType] = None
    sentiment_score: Optional[float] = None
    keywords: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Paginated message list response."""
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PublishRequest(BaseModel):
    """Publish request schema."""
    message_ids: list[int]
    target_platform: str
    options: dict = Field(default_factory=dict)


class PublishResponse(BaseModel):
    """Publish response schema."""
    success: bool
    message: str
    publish_records: list[dict] = Field(default_factory=list)


class WebhookPayload(BaseModel):
    """Webhook payload schema."""
    source: str
    event_type: str
    data: dict
    timestamp: Optional[datetime] = None
    signature: Optional[str] = None
