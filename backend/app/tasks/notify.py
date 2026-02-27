"""Notification Celery tasks."""
from app.tasks import celery_app
from app.database import async_session
from app.models import NotificationRecord, NotificationSetting, Message
from app.services.notifier import send_notification
from sqlalchemy import select
from datetime import datetime
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
def send_notification_task(self, record_id: int, content: str, title: str = None):
    """Send a single notification."""
    from app.database import async_session

    async def _send():
        async with async_session() as db:
            # Get record
            result = await db.execute(
                select(NotificationRecord).where(NotificationRecord.id == record_id)
            )
            record = result.scalar_one_or_none()

            if not record:
                return {"status": "error", "reason": "Notification record not found"}

            # Get user settings
            result = await db.execute(
                select(NotificationSetting).where(NotificationSetting.user_id == record.user_id)
            )
            settings = result.scalar_one_or_none()

            if not settings:
                record.status = "failed"
                record.error_message = "Notification settings not found"
                await db.commit()
                return {"status": "error", "reason": "Settings not found"}

            # Get destination
            if record.channel == "telegram":
                destination = settings.telegram_chat_id
            elif record.channel == "email":
                destination = settings.email_address
            else:
                record.status = "failed"
                record.error_message = f"Unknown channel: {record.channel}"
                await db.commit()
                return {"status": "error", "reason": "Unknown channel"}

            if not destination:
                record.status = "failed"
                record.error_message = f"Destination not configured for {record.channel}"
                await db.commit()
                return {"status": "error", "reason": "Destination not configured"}

            try:
                # Send notification
                await send_notification(
                    channel=record.channel,
                    to=destination,
                    content=content,
                    title=title,
                )

                record.status = "sent"
                record.sent_at = datetime.utcnow()
                await db.commit()

                return {
                    "status": "success",
                    "record_id": record_id,
                    "channel": record.channel,
                }

            except Exception as e:
                record.status = "failed"
                record.error_message = str(e)
                await db.commit()

                return {
                    "status": "error",
                    "record_id": record_id,
                    "error": str(e),
                }

    return run_async(_send())


@celery_app.task(bind=True)
def send_new_message_notifications(self):
    """Send notifications for new messages."""
    from app.database import async_session
    from app.models import MessageStatus

    async def _notify():
        async with async_session() as db:
            # Get new messages
            result = await db.execute(
                select(Message).where(Message.status == MessageStatus.NEW).limit(50)
            )
            messages = result.scalars().all()

            notified = 0
            for message in messages:
                # Get subscription and user
                from sqlalchemy.orm import selectinload

                result = await db.execute(
                    select(Message)
                    .options(selectinload(Message.subscription).selectinload("user"))
                    .where(Message.id == message.id)
                )
                msg_with_sub = result.scalar_one_or_none()

                if not msg_with_sub or not msg_with_sub.subscription:
                    continue

                user_id = msg_with_sub.subscription.user_id

                # Get user notification settings
                result = await db.execute(
                    select(NotificationSetting).where(NotificationSetting.user_id == user_id)
                )
                settings = result.scalar_one_or_none()

                if not settings or not settings.notify_on_new:
                    continue

                # Send notifications
                if settings.telegram_enabled and settings.telegram_chat_id:
                    record = NotificationRecord(
                        user_id=user_id,
                        message_id=message.id,
                        channel="telegram",
                        status="pending",
                    )
                    db.add(record)
                    await db.commit()

                    send_notification_task.delay(
                        record.id,
                        message.content,
                        message.title,
                    )
                    notified += 1

                if settings.email_enabled and settings.email_address:
                    record = NotificationRecord(
                        user_id=user_id,
                        message_id=message.id,
                        channel="email",
                        status="pending",
                    )
                    db.add(record)
                    await db.commit()

                    send_notification_task.delay(
                        record.id,
                        message.content,
                        message.title,
                    )
                    notified += 1

            return {"notified": notified, "messages_checked": len(messages)}

    return run_async(_notify())


@celery_app.task(bind=True)
def send_daily_digest(self):
    """Send daily digest emails."""
    from app.database import async_session
    from app.models import MessageStatus
    from app.services.notifier.email import send_digest_email

    async def _digest():
        async with async_session() as db:
            from datetime import timedelta

            # Get messages from last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)

            result = await db.execute(
                select(Message)
                .where(Message.created_at >= yesterday)
                .order_by(Message.created_at.desc())
                .limit(50)
            )
            messages = result.scalars().all()

            if not messages:
                return {"status": "skipped", "reason": "No messages to digest"}

            # Get all users with email notifications enabled
            result = await db.execute(
                select(NotificationSetting).where(NotificationSetting.email_enabled == True)
            )
            settings_list = result.scalars().all()

            sent_count = 0
            for settings in settings_list:
                try:
                    messages_data = [
                        {
                            "title": m.title,
                            "content": m.content,
                            "author": m.author,
                            "source_url": m.source_url,
                        }
                        for m in messages
                    ]

                    await send_digest_email(
                        to_email=settings.email_address,
                        messages=messages_data,
                        period="daily",
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"Error sending digest to {settings.email_address}: {e}")

            return {"sent": sent_count, "messages_included": len(messages)}

    return run_async(_digest())
