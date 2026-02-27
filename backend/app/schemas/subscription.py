"""Subscription schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.subscription import SourceType


class SubscriptionBase(BaseModel):
    """Base subscription schema."""
    name: str = Field(..., min_length=1, max_length=100)
    source_type: SourceType
    source_config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Subscription creation schema."""
    pass


class SubscriptionUpdate(BaseModel):
    """Subscription update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class SubscriptionResponse(SubscriptionBase):
    """Subscription response schema."""
    id: int
    user_id: int
    last_checked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TwitterConfig(BaseModel):
    """Twitter source configuration."""
    usernames: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class RSSConfig(BaseModel):
    """RSS source configuration."""
    url: str
    update_interval: int = Field(default=300, description="Update interval in seconds")


class WebhookConfig(BaseModel):
    """Webhook source configuration."""
    secret: Optional[str] = None
    allowed_ips: list[str] = Field(default_factory=list)


class KeywordConfig(BaseModel):
    """Keyword monitoring configuration."""
    keywords: list[str]
    sources: list[str] = Field(default_factory=list, description="Sources to monitor")
