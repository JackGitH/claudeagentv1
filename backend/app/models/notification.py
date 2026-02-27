"""Notification models."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class NotificationSetting(Base):
    """User notification settings."""
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    telegram_enabled = Column(Boolean, default=False)
    telegram_chat_id = Column(String(100), nullable=True)
    email_enabled = Column(Boolean, default=False)
    email_address = Column(String(100), nullable=True)
    notify_on_new = Column(Boolean, default=True)
    notify_on_keyword = Column(Boolean, default=True)
    quiet_hours_start = Column(String(5), default="22:00")
    quiet_hours_end = Column(String(5), default="08:00")
    filters = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="notification_settings")

    def __repr__(self):
        return f"<NotificationSetting(user_id={self.user_id})>"


class NotificationRecord(Base):
    """Record of sent notifications."""
    __tablename__ = "notification_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
    channel = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="notification_records")

    def __repr__(self):
        return f"<NotificationRecord(id={self.id}, channel='{self.channel}', status='{self.status}')>"
