"""Celery configuration."""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "message_subscription",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    # Beat schedule for periodic tasks
    beat_schedule={
        "collect-messages-every-5-minutes": {
            "task": "app.tasks.collect.collect_all_subscriptions",
            "schedule": 300.0,  # 5 minutes
        },
        "cleanup-old-messages-daily": {
            "task": "app.tasks.collect.cleanup_old_messages",
            "schedule": 86400.0,  # 24 hours
        },
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
