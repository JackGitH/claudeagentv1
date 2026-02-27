"""Message collector services."""
from app.services.collector.twitter import collect_from_subscription as collect_twitter
from app.services.collector.rss import collect_from_subscription as collect_rss
from app.services.collector.webhook import process_webhook
from app.services.collector.keyword import collect_from_subscription as collect_keyword
from app.models.subscription import SourceType

__all__ = [
    "collect_twitter",
    "collect_rss",
    "process_webhook",
    "collect_keyword",
    "collect_messages",
]


async def collect_messages(subscription, db):
    """Collect messages based on subscription source type."""
    collectors = {
        SourceType.TWITTER: collect_twitter,
        SourceType.RSS: collect_rss,
        SourceType.KEYWORD: collect_keyword,
    }

    collector = collectors.get(subscription.source_type)
    if collector:
        return await collector(subscription, db)

    return []
