"""Publishing background tasks."""
from typing import Dict, Any, List
import logging

from sqlalchemy import select
from app.database import async_session
from app.models import PublishRecord
from app.services.publisher import publish_message

logger = logging.getLogger(__name__)


async def publish_single_task(record_id: int) -> Dict[str, Any]:
    """Publish a single message."""
    async with async_session() as db:
        result = await db.execute(select(PublishRecord).where(PublishRecord.id == record_id))
        record = result.scalar_one_or_none()

        if not record:
            return {"status": "error", "reason": "Publish record not found"}

        updated_record = await publish_message(record, db)

        return {
            "status": updated_record.status,
            "record_id": record_id,
            "platform": updated_record.target_platform,
            "target_url": updated_record.target_url,
            "error": updated_record.error_message,
        }


async def publish_batch_task(record_ids: List[int]) -> Dict[str, Any]:
    """Publish multiple messages."""
    async with async_session() as db:
        results = []
        for record_id in record_ids:
            result = await db.execute(
                select(PublishRecord).where(PublishRecord.id == record_id)
            )
            record = result.scalar_one_or_none()

            if record:
                try:
                    updated = await publish_message(record, db)
                    results.append({
                        "record_id": record_id,
                        "status": updated.status,
                        "platform": updated.target_platform,
                    })
                except Exception as e:
                    logger.error(f"Error publishing record {record_id}: {e}")
                    results.append({
                        "record_id": record_id,
                        "status": "error",
                        "error": str(e),
                    })
            else:
                results.append({
                    "record_id": record_id,
                    "status": "error",
                    "error": "Record not found",
                })

        return {"results": results}


async def retry_failed_publishes_task() -> Dict[str, Any]:
    """Retry all failed publish records."""
    async with async_session() as db:
        result = await db.execute(
            select(PublishRecord).where(PublishRecord.status == "failed").limit(50)
        )
        failed_records = result.scalars().all()

        results = []
        for record in failed_records:
            try:
                updated = await publish_message(record, db)
                results.append({
                    "record_id": record.id,
                    "status": updated.status,
                })
            except Exception as e:
                logger.error(f"Error retrying record {record.id}: {e}")
                results.append({
                    "record_id": record.id,
                    "status": "still_failed",
                    "error": str(e),
                })

        return {"retried": len(failed_records), "results": results}