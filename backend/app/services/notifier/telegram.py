"""Telegram notification service."""
from typing import Optional
from app.config import settings
import asyncio

# Lazy import to avoid startup errors if not configured
_bot = None


def get_bot():
    """Get or create Telegram bot instance."""
    global _bot
    if _bot is None and settings.TELEGRAM_BOT_TOKEN:
        from telegram import Bot

        _bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    return _bot


async def send_telegram_message(
    chat_id: str,
    message: str,
    parse_mode: Optional[str] = "HTML",
) -> bool:
    """Send a message via Telegram Bot."""
    bot = get_bot()
    if not bot:
        raise ValueError("Telegram bot not configured")

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=parse_mode,
            disable_web_page_preview=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        raise


async def send_message_notification(
    chat_id: str,
    title: Optional[str],
    content: str,
    source_url: Optional[str] = None,
    author: Optional[str] = None,
) -> bool:
    """Send a formatted message notification."""
    # Format message
    parts = []

    if title:
        parts.append(f"<b>{title}</b>")

    if author:
        parts.append(f"👤 {author}")

    # Truncate content if too long
    max_length = 4000 - len("\n".join(parts)) - 10
    if len(content) > max_length:
        content = content[:max_length] + "..."

    parts.append(content)

    if source_url:
        parts.append(f'\n<a href="{source_url}">Read more</a>')

    message = "\n\n".join(parts)

    return await send_telegram_message(chat_id, message)


async def send_summary_notification(
    chat_id: str,
    summary_data: dict,
) -> bool:
    """Send a summary notification with multiple messages."""
    message = f"<b>📊 Message Summary</b>\n\n"
    message += f"Total new messages: {summary_data.get('total', 0)}\n"

    if summary_data.get("by_source"):
        message += "\nBy source:\n"
        for source, count in summary_data["by_source"].items():
            message += f"  • {source}: {count}\n"

    if summary_data.get("top_keywords"):
        message += "\nTop keywords:\n"
        for kw in summary_data["top_keywords"][:5]:
            message += f"  • {kw}\n"

    return await send_telegram_message(chat_id, message)


async def test_telegram_connection() -> bool:
    """Test Telegram bot connection."""
    bot = get_bot()
    if not bot:
        return False

    try:
        me = await bot.get_me()
        return bool(me)
    except Exception:
        return False
