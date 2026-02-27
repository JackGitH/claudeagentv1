"""Subscription model."""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class SourceType(str, enum.Enum):
    """Message source types."""
    TWITTER = "twitter"
    RSS = "rss"
    WEBHOOK = "webhook"
    KEYWORD = "keyword"


class Subscription(Base):
    """Subscription model for tracking message sources."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_config = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    messages = relationship("Message", back_populates="subscription", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subscription(id={self.id}, name='{self.name}', type='{self.source_type}')>"
