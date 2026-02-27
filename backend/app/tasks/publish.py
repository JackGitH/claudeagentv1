"""Publishing Celery tasks."""
from app.tasks import celery_app
from app.database import async_session
from app.models import PublishRecord, Message
from app.services.publisher import publish_message
from sqlalchemy import select
import asyncio


def run_async(coro):
    """Run async function in sync context for Celery."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True)
def publish_single(self, record_id: int):
    """Publish a single message."""
    from app.database import async_session

    async def _publish():
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

    return run_async(_publish())


@celery_app.task(bind=True)
def publish_batch(self, record_ids: list[int]):
    """Publish multiple messages."""
    from app.database import async_session

    async def _publish_batch():
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
                        results.append(
                            {
                                "record_id": record_id,
                                "status": updated.status,
                                "platform": updated.target_platform,
                            }
                        )
                    except Exception as e:
                        results.append(
                            {
                                "record_id": record_id,
                                "status": "error",
                                "error": str(e),
                            }
                        )
                else:
                    results.append(
                        {
                            "record_id": record_id,
                            "status": "error",
                            "error": "Record not found",
                        }
                    )

            return {"results": results}

    return run_async(_publish_batch())


@celery_app.task(bind=True)
def retry_failed_publishes(self):
    """Retry all failed publish records."""
    from app.database import async_session

    async def _retry():
        async with async_session() as db:
            result = await db.execute(
                select(PublishRecord).where(PublishRecord.status == "failed").limit(50)
            )
            failed_records = result.scalars().all()

            results = []
            for record in failed_records:
                try:
                    updated = await publish_message(record, db)
                    results.append(
                        {
                            "record_id": record.id,
                            "status": updated.status,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "record_id": record.id,
                            "status": "still_failed",
                            "error": str(e),
                        }
                    )

            return {"retried": len(failed_records), "results": results}

    return run_async(_retry())
