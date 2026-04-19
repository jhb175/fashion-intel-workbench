"""Celery application configuration — Redis as broker and result backend."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "fashion_intel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.tasks.aggregation_tasks.*": {"queue": "aggregation"},
        "app.tasks.ai_tasks.*": {"queue": "ai"},
        "app.tasks.briefing_tasks.*": {"queue": "ai"},
    },

    # Default queue for tasks without explicit routing
    task_default_queue="default",

    # Result expiration (24 hours)
    result_expires=86400,

    # Retry policy for broker connection
    broker_connection_retry_on_startup=True,
)

# Auto-discover task modules
celery_app.autodiscover_tasks(["app.tasks"])
