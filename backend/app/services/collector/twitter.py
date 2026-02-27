"""Twitter/X message collector."""
import tweepy
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Message, Subscription, MessageStatus


class TwitterCollector:
    """Twitter API client for collecting tweets."""

    def __init__(self):
        self.client = None
        self.api = None
        self._setup_client()

    def _setup_client(self):
        """Setup Twitter API client."""
        if not settings.TWITTER_BEARER_TOKEN:
            return

        # API v2 client
        self.client = tweepy.Client(
            bearer_token=settings.TWITTER_BEARER_TOKEN,
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token=settings.TWITTER_ACCESS_TOKEN,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        )

        # API v1.1 client (for some operations)
        if settings.TWITTER_API_KEY and settings.TWITTER_API_SECRET:
            auth = tweepy.OAuth1UserHandler(
                settings.TWITTER_API_KEY,
                settings.TWITTER_API_SECRET,
                settings.TWITTER_ACCESS_TOKEN,
                settings.TWITTER_ACCESS_TOKEN_SECRET,
            )
            self.api = tweepy.API(auth)

    async def collect_user_tweets(
        self,
        username: str,
        since_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[dict]:
        """Collect tweets from a specific user."""
        if not self.client:
            raise ValueError("Twitter API not configured")

        # Get user ID
        user = self.client.get_user(username=username)
        if not user.data:
            return []

        user_id = user.data.id

        # Get tweets
        tweets = self.client.get_users_tweets(
            id=user_id,
            max_results=max_results,
            since_id=since_id,
            tweet_fields=["created_at", "public_metrics", "entities", "context_annotations"],
            expansions=["author_id"],
            exclude=["retweets", "replies"],
        )

        if not tweets.data:
            return []

        return [
            {
                "id": str(tweet.id),
                "text": tweet.text,
                "created_at": tweet.created_at,
                "author": username,
                "url": f"https://twitter.com/{username}/status/{tweet.id}",
                "metrics": tweet.public_metrics if hasattr(tweet, "public_metrics") else {},
            }
            for tweet in tweets.data
        ]

    async def collect_by_keywords(
        self,
        keywords: List[str],
        since_id: Optional[str] = None,
        max_results: int = 100,
    ) -> List[dict]:
        """Collect tweets matching keywords."""
        if not self.client:
            raise ValueError("Twitter API not configured")

        query = " OR ".join(keywords) + " -is:retweet lang:en"

        tweets = self.client.search_recent_tweets(
            query=query,
            max_results=max_results,
            since_id=since_id,
            tweet_fields=["created_at", "public_metrics", "entities", "author_id"],
            expansions=["author_id"],
        )

        if not tweets.data:
            return []

        # Build author lookup
        authors = {}
        if tweets.includes and "users" in tweets.includes:
            authors = {u.id: u.username for u in tweets.includes["users"]}

        return [
            {
                "id": str(tweet.id),
                "text": tweet.text,
                "created_at": tweet.created_at,
                "author": authors.get(tweet.author_id, "unknown"),
                "url": f"https://twitter.com/{authors.get(tweet.author_id, 'i')}/status/{tweet.id}",
                "metrics": tweet.public_metrics if hasattr(tweet, "public_metrics") else {},
            }
            for tweet in tweets.data
        ]

    async def save_tweets(
        self,
        tweets: List[dict],
        subscription: Subscription,
        db: AsyncSession,
    ) -> List[Message]:
        """Save collected tweets to database."""
        messages = []

        for tweet in tweets:
            # Check if message already exists
            from sqlalchemy import select

            result = await db.execute(
                select(Message).where(Message.external_id == tweet["id"])
            )
            if result.scalar_one_or_none():
                continue

            message = Message(
                subscription_id=subscription.id,
                external_id=tweet["id"],
                content=tweet["text"],
                author=tweet["author"],
                source_url=tweet["url"],
                published_at=tweet["created_at"],
                status=MessageStatus.NEW,
            )
            db.add(message)
            messages.append(message)

        if messages:
            await db.commit()

        return messages


# Global collector instance
twitter_collector = TwitterCollector()


async def collect_from_subscription(subscription: Subscription, db: AsyncSession) -> List[Message]:
    """Collect messages from a Twitter subscription."""
    config = subscription.source_config
    collector = twitter_collector

    tweets = []
    since_id = config.get("last_tweet_id")

    # Collect by usernames
    usernames = config.get("usernames", [])
    for username in usernames:
        user_tweets = await collector.collect_user_tweets(username, since_id=since_id)
        tweets.extend(user_tweets)

    # Collect by keywords
    keywords = config.get("keywords", [])
    if keywords:
        keyword_tweets = await collector.collect_by_keywords(keywords, since_id=since_id)
        tweets.extend(keyword_tweets)

    # Save tweets
    messages = await collector.save_tweets(tweets, subscription, db)

    # Update last checked
    if tweets:
        max_id = max(int(t["id"]) for t in tweets)
        subscription.source_config["last_tweet_id"] = str(max_id)

    from datetime import datetime

    subscription.last_checked_at = datetime.utcnow()
    await db.commit()

    return messages
