"""Notification services."""
from app.services.notifier.telegram import (
    send_telegram_message,
    send_message_notification as send_telegram_notification,
    test_telegram_connection,
)
from app.services.notifier.email import (
    send_email,
    send_message_notification as send_email_notification,
    send_digest_email,
    test_email_connection,
)

__all__ = [
    "send_telegram_message",
    "send_telegram_notification",
    "test_telegram_connection",
    "send_email",
    "send_email_notification",
    "send_digest_email",
    "test_email_connection",
    "send_notification",
]


async def send_notification(
    channel: str,
    to: str,
    content: str,
    title: str = None,
    **kwargs,
) -> bool:
    """Send notification through specified channel."""
    if channel == "telegram":
        return await send_telegram_notification(
            chat_id=to,
            title=title,
            content=content,
            **kwargs,
        )
    elif channel == "email":
        return await send_email_notification(
            to_email=to,
            title=title,
            content=content,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown notification channel: {channel}")
