"""Email notification service."""
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
import aiosmtplib


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
) -> bool:
    """Send an email notification."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        raise ValueError("Email SMTP not configured")

    # Create message
    message = MIMEMultipart("alternative")
    message["From"] = settings.EMAIL_FROM or settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject

    # Add text body
    message.attach(MIMEText(body, "plain"))

    # Add HTML body if provided
    if html_body:
        message.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise


async def send_message_notification(
    to_email: str,
    title: Optional[str],
    content: str,
    source_url: Optional[str] = None,
    author: Optional[str] = None,
) -> bool:
    """Send a formatted message notification via email."""
    subject = title or "New Message Notification"

    # Plain text body
    text_body = ""
    if author:
        text_body += f"From: {author}\n\n"
    text_body += content
    if source_url:
        text_body += f"\n\nRead more: {source_url}"

    # HTML body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px;">
            <h2 style="color: #333;">{title or 'New Message'}</h2>
            {f'<p style="color: #666;">From: {author}</p>' if author else ''}
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p style="color: #333; line-height: 1.6;">{content[:1000]}{'...' if len(content) > 1000 else ''}</p>
            </div>
            {f'<a href="{source_url}" style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Read Full Article</a>' if source_url else ''}
        </div>
    </body>
    </html>
    """

    return await send_email(to_email, subject, text_body, html_body)


async def send_digest_email(
    to_email: str,
    messages: List[dict],
    period: str = "daily",
) -> bool:
    """Send a digest email with multiple messages."""
    subject = f"Your {period.capitalize()} Message Digest - {len(messages)} messages"

    # Plain text body
    text_body = f"Here's your {period} digest with {len(messages)} new messages:\n\n"
    for i, msg in enumerate(messages, 1):
        text_body += f"{i}. {msg.get('title', 'Untitled')}\n"
        text_body += f"   From: {msg.get('author', 'Unknown')}\n\n"

    # HTML body
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #f5f5f5; padding: 20px; border-radius: 10px;">
            <h2 style="color: #333;">Your {period.capitalize()} Digest</h2>
            <p style="color: #666;">{len(messages)} new messages</p>
    """

    for msg in messages:
        html_body += f"""
            <div style="background-color: white; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3 style="color: #333; margin-top: 0;">{msg.get('title', 'Untitled')}</h3>
                <p style="color: #666; font-size: 14px;">From: {msg.get('author', 'Unknown')}</p>
                <p style="color: #333; line-height: 1.6;">{msg.get('content', '')[:200]}...</p>
                {f'<a href="{msg.get("source_url")}" style="color: #007bff;">Read more</a>' if msg.get('source_url') else ''}
            </div>
        """

    html_body += """
        </div>
    </body>
    </html>
    """

    return await send_email(to_email, subject, text_body, html_body)


async def test_email_connection() -> bool:
    """Test email SMTP connection."""
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        return False

    try:
        await aiosmtplib.send(
            MIMEText("Test connection"),
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception:
        return False
