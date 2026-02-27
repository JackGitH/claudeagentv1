"""Webhook message collector."""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib
import json

from app.models import Message, Subscription, SourceType, MessageStatus
from app.schemas import WebhookPayload


async def find_webhook_subscription(
    source: str,
    db: AsyncSession,
) -> Optional[Subscription]:
    """Find subscription for webhook source."""
    result = await db.execute(
        select(Subscription).where(
            Subscription.source_type == SourceType.WEBHOOK,
            Subscription.enabled == True,
        )
    )
    subscriptions = result.scalars().all()

    # Find matching subscription by source name
    for sub in subscriptions:
        if sub.source_config.get("source") == source:
            return sub

    return None


async def process_webhook(
    payload: WebhookPayload,
    db: AsyncSession,
) -> Optional[Message]:
    """Process incoming webhook payload."""
    # Find subscription
    subscription = await find_webhook_subscription(payload.source, db)
    if not subscription:
        return None

    # Generate unique ID for webhook
    external_id = hashlib.sha256(
        f"{payload.source}:{payload.event_type}:{json.dumps(payload.data, sort_keys=True)}".encode()
    ).hexdigest()[:32]

    # Check if message already exists
    result = await db.execute(
        select(Message).where(Message.external_id == external_id)
    )
    if result.scalar_one_or_none():
        return None

    # Extract content from payload
    content = payload.data.get("content", payload.data.get("text", payload.data.get("body", "")))
    title = payload.data.get("title", payload.data.get("subject", None))
    author = payload.data.get("author", payload.data.get("user", payload.source))
    url = payload.data.get("url", payload.data.get("link", None))

    if not content:
        return None

    # Create message
    message = Message(
        subscription_id=subscription.id,
        external_id=external_id,
        title=title,
        content=content,
        author=author,
        source_url=url,
        published_at=payload.timestamp or datetime.utcnow(),
        status=MessageStatus.NEW,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


async def verify_webhook_signature(
    payload: str,
    signature: str,
    secret: str,
) -> bool:
    """Verify webhook signature."""
    import hmac

    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
