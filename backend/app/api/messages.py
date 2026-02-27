"""Messages API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import math

from app.database import get_db
from app.models import User, Message, Subscription, MessageStatus
from app.schemas import (
    MessageCreate,
    MessageResponse,
    MessageListResponse,
    WebhookPayload,
)
from app.api.auth import get_current_active_user
from app.services.collector.webhook import process_webhook

router = APIRouter()


@router.get("", response_model=MessageListResponse)
async def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subscription_id: Optional[int] = None,
    status: Optional[MessageStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List messages with pagination and filters."""
    # Base query - join with subscriptions to filter by user
    query = (
        select(Message)
        .join(Subscription)
        .where(Subscription.user_id == current_user.id)
    )

    # Apply filters
    if subscription_id:
        query = query.where(Message.subscription_id == subscription_id)

    if status:
        query = query.where(Message.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Message.title.ilike(search_term),
                Message.content.ilike(search_term),
                Message.author.ilike(search_term),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Message.created_at.desc())

    # Execute query
    result = await db.execute(query)
    messages = result.scalars().all()

    return MessageListResponse(
        items=messages,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific message."""
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

    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a message."""
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

    await db.delete(message)
    await db.commit()

    return None


@router.post("/webhook", status_code=status.HTTP_201_CREATED)
async def receive_webhook(
    payload: WebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """Receive webhook message."""
    # Process webhook payload
    message = await process_webhook(payload, db)

    if message:
        return {"status": "success", "message_id": message.id}

    return {"status": "ignored"}


@router.post("/{message_id}/analyze", response_model=MessageResponse)
async def analyze_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI analysis for a message."""
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

    # Import and run analysis
    from app.services.ai.analyzer import analyze_message as run_analysis

    analyzed_message = await run_analysis(message, db)

    return analyzed_message
