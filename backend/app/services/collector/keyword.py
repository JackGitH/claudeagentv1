"""Keyword monitoring collector."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import hashlib

from app.models import Message, Subscription, MessageStatus
from app.config import settings


class KeywordMonitor:
    """Monitor keywords across multiple sources."""

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def search_twitter(self, keywords: List[str], since_id: Optional[str] = None) -> List[dict]:
        """Search Twitter for keywords (via Twitter API)."""
        from app.services.collector.twitter import twitter_collector

        if twitter_collector.client:
            return await twitter_collector.collect_by_keywords(keywords, since_id=since_id)
        return []

    async def search_rss_feeds(
        self,
        feeds: List[str],
        keywords: List[str],
    ) -> List[dict]:
        """Search RSS feeds for keywords."""
        from app.services.collector.rss import rss_collector

        results = []
        keywords_lower = [k.lower() for k in keywords]

        for feed_url in feeds:
            try:
                feed = await rss_collector.fetch_feed(feed_url)
                for entry in feed.entries:
                    title = entry.get("title", "").lower()
                    content = entry.get("summary", entry.get("description", "")).lower()

                    # Check if any keyword matches
                    if any(kw in title or kw in content for kw in keywords_lower):
                        published_at = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_at = datetime(*entry.published_parsed[:6])

                        results.append(
                            {
                                "id": entry.get("guid", entry.get("link", "")),
                                "title": entry.get("title", ""),
                                "content": entry.get("summary", entry.get("description", "")),
                                "author": entry.get("author", feed.feed.get("title", "")),
                                "source_url": entry.get("link", ""),
                                "published_at": published_at,
                                "source": "rss",
                            }
                        )
            except Exception as e:
                print(f"Error fetching feed {feed_url}: {e}")
                continue

        return results

    async def search_custom_sources(
        self,
        sources: List[str],
        keywords: List[str],
    ) -> List[dict]:
        """Search custom sources (e.g., APIs) for keywords."""
        results = []
        keywords_lower = [k.lower() for k in keywords]

        for source in sources:
            try:
                # Generic API search - can be extended for specific sources
                if source.startswith("http"):
                    response = await self.http_client.get(source)
                    if response.status_code == 200:
                        data = response.json()
                        # Parse based on common formats
                        items = data.get("items", data.get("results", data.get("data", [])))
                        for item in items:
                            title = item.get("title", "")
                            content = item.get("content", item.get("description", item.get("body", "")))

                            if any(kw in title.lower() or kw in content.lower() for kw in keywords_lower):
                                results.append(
                                    {
                                        "id": str(item.get("id", "")),
                                        "title": title,
                                        "content": content,
                                        "author": item.get("author", ""),
                                        "source_url": item.get("url", source),
                                        "published_at": item.get("published_at", item.get("created_at")),
                                        "source": "custom",
                                    }
                                )
            except Exception as e:
                print(f"Error searching source {source}: {e}")
                continue

        return results

    async def save_results(
        self,
        results: List[dict],
        subscription: Subscription,
        db: AsyncSession,
    ) -> List[Message]:
        """Save keyword monitoring results to database."""
        messages = []

        for result in results:
            # Generate unique ID
            external_id = result.get("id") or hashlib.md5(
                f"{result.get('source')}:{result.get('title')}:{result.get('published_at')}".encode()
            ).hexdigest()

            # Check if message already exists
            query = select(Message).where(Message.external_id == external_id)
            result_db = await db.execute(query)
            if result_db.scalar_one_or_none():
                continue

            message = Message(
                subscription_id=subscription.id,
                external_id=external_id,
                title=result.get("title"),
                content=result.get("content", ""),
                author=result.get("author"),
                source_url=result.get("source_url"),
                published_at=result.get("published_at"),
                status=MessageStatus.NEW,
            )
            db.add(message)
            messages.append(message)

        if messages:
            await db.commit()

        return messages


# Global monitor instance
keyword_monitor = KeywordMonitor()


async def collect_from_subscription(subscription: Subscription, db: AsyncSession) -> List[Message]:
    """Collect messages from a keyword monitoring subscription."""
    config = subscription.source_config
    monitor = keyword_monitor

    keywords = config.get("keywords", [])
    sources = config.get("sources", [])

    if not keywords:
        return []

    results = []
    since_id = config.get("last_id")

    # Search Twitter if API configured
    if "twitter" in sources or not sources:
        twitter_results = await monitor.search_twitter(keywords, since_id=since_id)
        results.extend(twitter_results)

    # Search RSS feeds
    rss_feeds = config.get("rss_feeds", [])
    if rss_feeds:
        rss_results = await monitor.search_rss_feeds(rss_feeds, keywords)
        results.extend(rss_results)

    # Search custom sources
    custom_sources = config.get("custom_sources", [])
    if custom_sources:
        custom_results = await monitor.search_custom_sources(custom_sources, keywords)
        results.extend(custom_results)

    # Save results
    messages = await monitor.save_results(results, subscription, db)

    # Update last checked
    if results:
        max_id = max(r.get("id", "") for r in results if r.get("id"))
        if max_id:
            subscription.source_config["last_id"] = max_id

    subscription.last_checked_at = datetime.utcnow()
    await db.commit()

    return messages
