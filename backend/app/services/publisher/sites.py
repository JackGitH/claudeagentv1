"""Publishing service for external platforms."""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.models import PublishRecord, Message


class BasePublisher:
    """Base class for publishers."""

    platform_name: str = "base"

    async def publish(self, message: Message, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Publish a message to the platform."""
        raise NotImplementedError


class WebhookPublisher(BasePublisher):
    """Publish to a webhook endpoint."""

    platform_name = "webhook"

    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}

    async def publish(self, message: Message, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send message to webhook."""
        async with httpx.AsyncClient() as client:
            payload = {
                "title": message.title,
                "content": message.content,
                "author": message.author,
                "source_url": message.source_url,
                "published_at": message.published_at.isoformat() if message.published_at else None,
                "metadata": options or {},
            }

            response = await client.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
            )

            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response": response.text[:500],
            }


class TelegramChannelPublisher(BasePublisher):
    """Publish to a Telegram channel."""

    platform_name = "telegram_channel"

    def __init__(self, channel_id: str):
        self.channel_id = channel_id

    async def publish(self, message: Message, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Post message to Telegram channel."""
        from app.services.notifier.telegram import send_telegram_message

        # Format message
        text = ""
        if message.title:
            text += f"<b>{message.title}</b>\n\n"
        text += message.content
        if message.source_url:
            text += f'\n\n<a href="{message.source_url}">Source</a>'

        try:
            await send_telegram_message(self.channel_id, text)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


class EmailPublisher(BasePublisher):
    """Publish via email newsletter."""

    platform_name = "email"

    def __init__(self, recipients: list[str]):
        self.recipients = recipients

    async def publish(self, message: Message, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send message as email."""
        from app.services.notifier.email import send_message_notification

        results = []
        for recipient in self.recipients:
            try:
                await send_message_notification(
                    to_email=recipient,
                    title=message.title,
                    content=message.content,
                    source_url=message.source_url,
                    author=message.author,
                )
                results.append({"email": recipient, "success": True})
            except Exception as e:
                results.append({"email": recipient, "success": False, "error": str(e)})

        all_success = all(r["success"] for r in results)
        return {"success": all_success, "results": results}


# Publisher registry
_publishers = {}


def register_publisher(platform: str, publisher: BasePublisher):
    """Register a publisher instance."""
    _publishers[platform] = publisher


def get_publisher(platform: str) -> Optional[BasePublisher]:
    """Get a registered publisher."""
    return _publishers.get(platform)


async def publish_message(
    record: PublishRecord,
    db: AsyncSession,
) -> PublishRecord:
    """Publish a message using the publish record."""
    # Get the message
    message = record.message

    # Get publisher
    publisher = get_publisher(record.target_platform)
    if not publisher:
        record.status = "failed"
        record.error_message = f"No publisher registered for platform: {record.target_platform}"
        await db.commit()
        return record

    try:
        # Publish
        result = await publisher.publish(message)

        if result.get("success"):
            record.status = "published"
            record.published_at = datetime.utcnow()
            if result.get("url"):
                record.target_url = result["url"]
        else:
            record.status = "failed"
            record.error_message = result.get("error", "Unknown error")

    except Exception as e:
        record.status = "failed"
        record.error_message = str(e)

    await db.commit()
    return record
