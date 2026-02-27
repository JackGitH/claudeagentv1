"""Notifications API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import User, NotificationSetting, NotificationRecord
from app.schemas import (
    NotificationSettingCreate,
    NotificationSettingUpdate,
    NotificationSettingResponse,
    NotificationRecordResponse,
    NotifyRequest,
)
from app.api.auth import get_current_active_user

router = APIRouter()


@router.get("/settings", response_model=NotificationSettingResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notification settings for current user."""
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings
        settings = NotificationSetting(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings


@router.put("/settings", response_model=NotificationSettingResponse)
async def update_notification_settings(
    settings_data: NotificationSettingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update notification settings for current user."""
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        settings = NotificationSetting(user_id=current_user.id)
        db.add(settings)

    # Update fields
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return settings


@router.post("/notify", response_model=dict)
async def send_notification(
    request: NotifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a notification to specified channels."""
    # Get user settings
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification settings not configured",
        )

    # Create notification records
    records = []
    for channel in request.channels:
        if channel == "telegram" and not settings.telegram_enabled:
            continue
        if channel == "email" and not settings.email_enabled:
            continue

        record = NotificationRecord(
            user_id=current_user.id,
            message_id=request.message_id,
            channel=channel,
            status="pending",
        )
        db.add(record)
        records.append(record)

    await db.commit()

    # TODO: Trigger actual notification via Celery task
    # from app.tasks.notify import send_notifications
    # send_notifications.delay([r.id for r in records], request.content)

    return {
        "success": True,
        "message": f"Queued {len(records)} notifications",
        "channels": request.channels,
    }


@router.get("/records", response_model=List[NotificationRecordResponse])
async def list_notification_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List notification records for current user."""
    result = await db.execute(
        select(NotificationRecord)
        .where(NotificationRecord.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(NotificationRecord.created_at.desc())
    )
    records = result.scalars().all()

    return records


@router.post("/telegram/test")
async def test_telegram(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Test Telegram notification."""
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings or not settings.telegram_enabled or not settings.telegram_chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telegram not configured",
        )

    # Send test message
    try:
        from app.services.notifier.telegram import send_telegram_message

        await send_telegram_message(
            settings.telegram_chat_id,
            "🔔 Test notification from Message Subscription System",
        )
        return {"success": True, "message": "Test message sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test message: {str(e)}",
        )


@router.post("/email/test")
async def test_email(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Test email notification."""
    result = await db.execute(
        select(NotificationSetting).where(NotificationSetting.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if not settings or not settings.email_enabled or not settings.email_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not configured",
        )

    # Send test email
    try:
        from app.services.notifier.email import send_email

        await send_email(
            to_email=settings.email_address,
            subject="Test Notification",
            body="This is a test notification from Message Subscription System",
        )
        return {"success": True, "message": "Test email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}",
        )
