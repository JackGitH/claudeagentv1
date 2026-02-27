"""Message and related models."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MessageStatus(str, enum.Enum):
    """Message processing status."""
    NEW = "new"
    PROCESSING = "processing"
    PROCESSED = "processed"
    PUBLISHED = "published"
    FAILED = "failed"


class SentimentType(str, enum.Enum):
    """Sentiment analysis result."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class Message(Base):
    """Message model for storing collected messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String(255), index=True, nullable=True)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=True)
    author = Column(String(100), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.NEW)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # AI Analysis fields
    summary = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    sentiment = Column(SQLEnum(SentimentType), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    keywords = Column(String(500), nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="messages")
    publish_records = relationship("PublishRecord", back_populates="message", cascade="all, delete-orphan")
    notification_records = relationship("NotificationRecord", back_populates="message", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Message(id={self.id}, title='{self.title[:30] if self.title else ''}...')>"


class PublishRecord(Base):
    """Record of message publishing to external platforms."""
    __tablename__ = "publish_records"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    target_platform = Column(String(50), nullable=False)
    target_url = Column(String(1000), nullable=True)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="publish_records")

    def __repr__(self):
        return f"<PublishRecord(id={self.id}, platform='{self.target_platform}', status='{self.status}')>"
