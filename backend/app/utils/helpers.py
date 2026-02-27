"""Utility helper functions."""
from datetime import datetime
from typing import Optional


def format_datetime(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    if not dt:
        return ""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse string to datetime."""
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        return None


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if not text or len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re

    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        return parsed.netloc
    except Exception:
        return ""


def generate_hash(text: str) -> str:
    """Generate MD5 hash of text."""
    import hashlib

    return hashlib.md5(text.encode()).hexdigest()


def is_quiet_hours(start_hour: int, end_hour: int, current_hour: int = None) -> bool:
    """Check if current time is within quiet hours."""
    if current_hour is None:
        current_hour = datetime.now().hour

    if start_hour <= end_hour:
        return start_hour <= current_hour < end_hour
    else:  # Quiet hours span midnight
        return current_hour >= start_hour or current_hour < end_hour
