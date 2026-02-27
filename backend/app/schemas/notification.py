"""Notification schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class NotificationSettingBase(BaseModel):
    """Base notification settings schema."""
    telegram_enabled: bool = False
    telegram_chat_id: Optional[str] = None
    email_enabled: bool = False
    email_address: Optional[EmailStr] = None
    notify_on_new: bool = True
    notify_on_keyword: bool = True
    quiet_hours_start: str = "22:00"
    quiet_hours_end: str = "08:00"
    filters: Dict[str, Any] = Field(default_factory=dict)


class NotificationSettingCreate(NotificationSettingBase):
    """Notification settings creation schema."""
    pass


class NotificationSettingUpdate(BaseModel):
    """Notification settings update schema."""
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    email_enabled: Optional[bool] = None
    email_address: Optional[EmailStr] = None
    notify_on_new: Optional[bool] = None
    notify_on_keyword: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class NotificationSettingResponse(NotificationSettingBase):
    """Notification settings response schema."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationRecordResponse(BaseModel):
    """Notification record response schema."""
    id: int
    user_id: int
    message_id: Optional[int] = None
    channel: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotifyRequest(BaseModel):
    """Notify request schema."""
    message_id: Optional[int] = None
    content: str
    channels: list[str] = Field(default_factory=lambda: ["telegram", "email"])
