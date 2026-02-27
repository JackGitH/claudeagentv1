"""Publish API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database import get_db
from app.models import User, Message, Subscription, PublishRecord
from app.schemas import PublishRequest, PublishResponse
from app.api.auth import get_current_active_user

router = APIRouter()


@router.post("", response_model=PublishResponse)
async def publish_messages(
    request: PublishRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish multiple messages to target platform."""
    # Verify all messages belong to user
    result = await db.execute(
        select(Message)
        .join(Subscription)
        .where(
            Message.id.in_(request.message_ids),
            Subscription.user_id == current_user.id,
        )
    )
    messages = result.scalars().all()

    if len(messages) != len(request.message_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some messages not found or not accessible",
        )

    # Create publish records
    publish_records = []
    for message in messages:
        record = PublishRecord(
            message_id=message.id,
            target_platform=request.target_platform,
            status="pending",
        )
        db.add(record)
        publish_records.append(record)

    await db.commit()

    # TODO: Trigger actual publishing via Celery task
    # from app.tasks.publish import publish_to_platform
    # publish_to_platform.delay([r.id for r in publish_records], request.target_platform, request.options)

    return PublishResponse(
        success=True,
        message=f"Queued {len(publish_records)} messages for publishing to {request.target_platform}",
        publish_records=[
            {
                "id": r.id,
                "message_id": r.message_id,
                "status": r.status,
                "platform": r.target_platform,
            }
            for r in publish_records
        ],
    )


@router.post("/{message_id}", response_model=PublishResponse)
async def publish_single_message(
    message_id: int,
    target_platform: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a single message to target platform."""
    # Verify message belongs to user
    result = await db.execute(
        select(Message)
        .join(Subscription)
        .where(
            Message.id == message_id,
            Subscription.user_id == current_user.id,
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Create publish record
    record = PublishRecord(
        message_id=message.id,
        target_platform=target_platform,
        status="pending",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # TODO: Trigger actual publishing via Celery task

    return PublishResponse(
        success=True,
        message=f"Message {message_id} queued for publishing to {target_platform}",
        publish_records=[
            {
                "id": record.id,
                "message_id": record.message_id,
                "status": record.status,
                "platform": record.target_platform,
            }
        ],
    )


@router.get("/records", response_model=List[dict])
async def list_publish_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List publish records for current user."""
    result = await db.execute(
        select(PublishRecord)
        .join(Message)
        .join(Subscription)
        .where(Subscription.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .order_by(PublishRecord.created_at.desc())
    )
    records = result.scalars().all()

    return [
        {
            "id": r.id,
            "message_id": r.message_id,
            "platform": r.target_platform,
            "status": r.status,
            "target_url": r.target_url,
            "error_message": r.error_message,
            "published_at": r.published_at,
            "created_at": r.created_at,
        }
        for r in records
    ]
