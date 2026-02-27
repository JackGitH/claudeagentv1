"""Message collection Celery tasks."""
from app.tasks import celery_app
from app.database import async_session
from app.models import Subscription, Message
from app.services.collector import collect_messages
from sqlalchemy import select
from datetime import datetime, timedelta
import asyncio


def run_async(coro):
    """Run async function in sync context for Celery."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True)
def collect_subscription(self, subscription_id: int):
    """Collect messages for a single subscription."""
    from app.database import async_session

    async def _collect():
        async with async_session() as db:
            # Get subscription
            result = await db.execute(select(Subscription).where(Subscription.id == subscription_id))
            subscription = result.scalar_one_or_none()

            if not subscription or not subscription.enabled:
                return {"status": "skipped", "reason": "Subscription not found or disabled"}

            # Collect messages
            messages = await collect_messages(subscription, db)

            return {
                "status": "success",
                "subscription_id": subscription_id,
                "messages_collected": len(messages),
                "message_ids": [m.id for m in messages],
            }

    return run_async(_collect())


@celery_app.task(bind=True)
def collect_all_subscriptions(self):
    """Collect messages for all enabled subscriptions."""
    from app.database import async_session

    async def _collect_all():
        async with async_session() as db:
            # Get all enabled subscriptions
            result = await db.execute(select(Subscription).where(Subscription.enabled == True))
            subscriptions = result.scalars().all()

            results = []
            for subscription in subscriptions:
                try:
                    messages = await collect_messages(subscription, db)
                    results.append(
                        {
                            "subscription_id": subscription.id,
                            "status": "success",
                            "messages_collected": len(messages),
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "subscription_id": subscription.id,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            return {
                "total_subscriptions": len(subscriptions),
                "results": results,
            }

    return run_async(_collect_all())


@celery_app.task(bind=True)
def analyze_message_task(self, message_id: int):
    """Analyze a single message with AI."""
    from app.database import async_session
    from app.services.ai import analyze_message

    async def _analyze():
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

    return run_async(_analyze())


@celery_app.task(bind=True)
def analyze_new_messages(self):
    """Analyze all new messages."""
    from app.database import async_session
    from app.models import MessageStatus

    async def _analyze_all():
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
                    print(f"Error analyzing message {message.id}: {e}")

            return {"analyzed": analyzed_count, "total": len(messages)}

    return run_async(_analyze_all())


@celery_app.task(bind=True)
def cleanup_old_messages(self, days: int = 30):
    """Delete messages older than specified days."""
    from app.database import async_session

    async def _cleanup():
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

    return run_async(_cleanup())
