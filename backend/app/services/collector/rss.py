"""RSS feed collector."""
import feedparser
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.models import Message, Subscription, MessageStatus


class RSSCollector:
    """RSS feed collector."""

    async def fetch_feed(self, url: str) -> feedparser.FeedParserDict:
        """Fetch and parse RSS feed."""
        return feedparser.parse(url)

    async def parse_entries(
        self,
        feed: feedparser.FeedParserDict,
        since_guid: Optional[str] = None,
    ) -> List[dict]:
        """Parse feed entries into messages."""
        entries = []

        for entry in feed.entries:
            # Skip if already processed
            if since_guid and entry.get("guid", entry.get("link")) == since_guid:
                break

            # Generate unique ID
            guid = entry.get("guid", entry.get("link", ""))
            if not guid:
                guid = hashlib.md5(entry.get("title", "").encode()).hexdigest()

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6])

            # Get content
            content = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            if not content:
                content = entry.get("summary", entry.get("description", ""))

            entries.append(
                {
                    "guid": guid,
                    "title": entry.get("title", ""),
                    "content": content,
                    "author": entry.get("author", feed.feed.get("title", "")),
                    "source_url": entry.get("link", ""),
                    "published_at": published_at,
                }
            )

        return entries

    async def save_entries(
        self,
        entries: List[dict],
        subscription: Subscription,
        db: AsyncSession,
    ) -> List[Message]:
        """Save feed entries to database."""
        messages = []

        for entry in entries:
            # Check if message already exists
            result = await db.execute(
                select(Message).where(Message.external_id == entry["guid"])
            )
            if result.scalar_one_or_none():
                continue

            message = Message(
                subscription_id=subscription.id,
                external_id=entry["guid"],
                title=entry["title"],
                content=entry["content"],
                author=entry["author"],
                source_url=entry["source_url"],
                published_at=entry["published_at"],
                status=MessageStatus.NEW,
            )
            db.add(message)
            messages.append(message)

        if messages:
            await db.commit()

        return messages


# Global collector instance
rss_collector = RSSCollector()


async def collect_from_subscription(subscription: Subscription, db: AsyncSession) -> List[Message]:
    """Collect messages from an RSS subscription."""
    config = subscription.source_config
    collector = rss_collector

    url = config.get("url")
    if not url:
        return []

    # Fetch feed
    feed = await collector.fetch_feed(url)

    # Get last processed GUID
    since_guid = config.get("last_guid")

    # Parse entries
    entries = await collector.parse_entries(feed, since_guid=since_guid)

    # Save entries
    messages = await collector.save_entries(entries, subscription, db)

    # Update last processed GUID
    if entries:
        subscription.source_config["last_guid"] = entries[0]["guid"]

    subscription.last_checked_at = datetime.utcnow()
    await db.commit()

    return messages
