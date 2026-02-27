"""AI message analysis service using OpenAI."""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.config import settings
from app.models import Message, SentimentType


# Initialize OpenAI client
_client = None


def get_client():
    """Get or create OpenAI client."""
    global _client
    if _client is None and settings.OPENAI_API_KEY:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def generate_summary(content: str, max_length: int = 200) -> str:
    """Generate a summary of the message content."""
    client = get_client()
    if not client:
        return None

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes text concisely. Provide a brief, informative summary.",
                },
                {
                    "role": "user",
                    "content": f"Summarize the following text in {max_length} characters or less:\n\n{content[:4000]}",
                },
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None


async def classify_content(content: str, categories: List[str] = None) -> str:
    """Classify the content into a category."""
    client = get_client()
    if not client:
        return None

    if categories is None:
        categories = [
            "Technology",
            "Business",
            "Politics",
            "Sports",
            "Entertainment",
            "Science",
            "Health",
            "Finance",
            "Other",
        ]

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a classifier. Classify text into one of these categories: {', '.join(categories)}. Reply with only the category name.",
                },
                {
                    "role": "user",
                    "content": f"Classify this text:\n\n{content[:2000]}",
                },
            ],
            max_tokens=20,
            temperature=0.1,
        )
        category = response.choices[0].message.content.strip()
        return category if category in categories else "Other"
    except Exception as e:
        print(f"Error classifying content: {e}")
        return None


async def analyze_sentiment(content: str) -> Dict[str, Any]:
    """Analyze the sentiment of the content."""
    client = get_client()
    if not client:
        return None

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a sentiment analyzer. Analyze the sentiment and respond in JSON format with 'sentiment' (positive, negative, or neutral) and 'score' (0.0 to 1.0).",
                },
                {
                    "role": "user",
                    "content": f"Analyze the sentiment of this text:\n\n{content[:2000]}",
                },
            ],
            max_tokens=50,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        import json

        result = json.loads(response.choices[0].message.content)
        return {
            "sentiment": SentimentType(result["sentiment"].lower()),
            "score": float(result["score"]),
        }
    except Exception as e:
        print(f"Error analyzing sentiment: {e}")
        return None


async def extract_keywords(content: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from the content."""
    client = get_client()
    if not client:
        return []

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a keyword extractor. Extract the most important keywords. Respond with a JSON array of strings.",
                },
                {
                    "role": "user",
                    "content": f"Extract up to {max_keywords} keywords from this text:\n\n{content[:2000]}",
                },
            ],
            max_tokens=100,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        import json

        result = json.loads(response.choices[0].message.content)
        return result.get("keywords", result.get("list", []))
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return []


async def analyze_message(message: Message, db: AsyncSession) -> Message:
    """Perform full AI analysis on a message."""
    content = message.content
    if message.title:
        content = f"{message.title}\n\n{content}"

    # Run all analyses
    summary_task = generate_summary(content)
    category_task = classify_content(content)
    sentiment_task = analyze_sentiment(content)
    keywords_task = extract_keywords(content)

    # Wait for all results
    summary, category, sentiment, keywords = await asyncio.gather(
        summary_task, category_task, sentiment_task, keywords_task
    )

    # Update message
    message.summary = summary
    message.category = category
    if sentiment:
        message.sentiment = sentiment["sentiment"]
        message.sentiment_score = sentiment["score"]
    message.keywords = ",".join(keywords) if keywords else None

    # Save changes
    await db.commit()
    await db.refresh(message)

    return message


import asyncio
