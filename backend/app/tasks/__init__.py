"""Background tasks using FastAPI BackgroundTasks."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging

from sqlalchemy import select
from app.database import async_session
from app.models import Subscription, Message, MessageStatus
from app.services.collector import collect_messages
from app.services.ai import analyze_message

logger = logging.getLogger(__name__)


async def collect_subscription_task(subscription_id: int) -> Dict[str, Any]:
    """Collect messages for a single subscription."""
    async with async_session() as db:
        result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
        subscription = result.scalar_one_or_none()

        if not subscription or not subscription.enabled:
            return {"status": "skipped", "reason": "Subscription not found or disabled"}

        messages = await collect_messages(subscription, db)

        return {
            "status": "success",
            "subscription_id": subscription_id,
            "messages_collected": len(messages),
            "message_ids": [m.id for m in messages],
        }


async def collect_all_subscriptions_task() -> Dict[str, Any]:
    """Collect messages for all enabled subscriptions."""
    async with async_session() as db:
        result = await db.execute(select(Subscription).where(Subscription.enabled == True))
        subscriptions = result.scalars().all()

        results = []
        for subscription in subscriptions:
            try:
                messages = await collect_messages(subscription, db)
                results.append({
                    "subscription_id": subscription.id,
                    "status": "success",
                    "messages_collected": len(messages),
                })
            except Exception as e:
                logger.error(f"Error collecting subscription {subscription.id}: {e}")
                results.append({
                    "subscription_id": subscription.id,
                    "status": "error",
                    "error": str(e),
                })

        return {
            "total_subscriptions": len(subscriptions),
            "results": results,
        }


async def analyze_message_task(message_id: int) -> Dict[str, Any]:
    """Analyze a single message with AI."""
    async with async_session() as db:
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalar_one_or_none()

        if not message:
            return {"status": "error", "reason": "Message not found"}

        analyzed = await analyze_message(message, db)

        return {
            "status": "success",
            "message_id": message_id,
            "summary": analyzed.summary,
            "category": analyzed.category,
            "sentiment": analyzed.sentiment.value if analyzed.sentiment else None,
        }


async def analyze_new_messages_task() -> Dict[str, Any]:
    """Analyze all new messages."""
    async with async_session() as db:
        result = await db.execute(
            select(Message).where(Message.status == MessageStatus.NEW).limit(100)
        )
        messages = result.scalars().all()

        analyzed_count = 0
        for message in messages:
            try:
                await analyze_message(message, db)
                analyzed_count += 1
            except Exception as e:
                logger.error(f"Error analyzing message {message.id}: {e}")

        return {"analyzed": analyzed_count, "total": len(messages)}


async def cleanup_old_messages_task(days: int = 30) -> Dict[str, Any]:
    """Delete messages older than specified days."""
    async with async_session() as db:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(Message).where(Message.created_at < cutoff_date)
        )
        old_messages = result.scalars().all()

        count = len(old_messages)
        for message in old_messages:
            await db.delete(message)

        await db.commit()

        return {"deleted": count, "older_than_days": days}