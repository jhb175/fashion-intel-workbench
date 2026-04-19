"""APScheduler integration — periodic collection task scheduling.

The scheduler is started when the FastAPI app starts (via lifespan) and
shut down gracefully when the app stops.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Default collection interval in minutes (can be overridden via env)
_DEFAULT_INTERVAL_MINUTES = 60

# Default daily briefing generation hour (UTC, can be overridden via env)
_DEFAULT_BRIEFING_HOUR = 8
_DEFAULT_BRIEFING_MINUTE = 0

_scheduler: BackgroundScheduler | None = None


def _dispatch_collection_task() -> None:
    """Callback invoked by APScheduler — dispatches the Celery collection task."""
    try:
        from app.tasks.aggregation_tasks import run_scheduled_collection

        run_scheduled_collection.delay()
        logger.info("Dispatched scheduled collection task via APScheduler")
    except Exception:
        logger.exception("Failed to dispatch scheduled collection task")


def _dispatch_daily_briefing_task() -> None:
    """Callback invoked by APScheduler — dispatches the Celery daily briefing task."""
    try:
        from app.tasks.briefing_tasks import generate_daily_briefing_task

        generate_daily_briefing_task.delay()
        logger.info("Dispatched daily briefing generation task via APScheduler")
    except Exception:
        logger.exception("Failed to dispatch daily briefing task")


def start_scheduler(interval_minutes: int = _DEFAULT_INTERVAL_MINUTES) -> BackgroundScheduler:
    """Create and start the APScheduler background scheduler.

    Args:
        interval_minutes: How often (in minutes) to trigger collection.

    Returns:
        The running ``BackgroundScheduler`` instance.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler is already running — skipping start")
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _dispatch_collection_task,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="scheduled_collection",
        name="Periodic article collection",
        replace_existing=True,
    )
    _scheduler.add_job(
        _dispatch_daily_briefing_task,
        trigger=CronTrigger(hour=_DEFAULT_BRIEFING_HOUR, minute=_DEFAULT_BRIEFING_MINUTE),
        id="daily_briefing_generation",
        name="Daily briefing generation",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "APScheduler started — collection every %d minutes, daily briefing at %02d:%02d UTC",
        interval_minutes,
        _DEFAULT_BRIEFING_HOUR,
        _DEFAULT_BRIEFING_MINUTE,
    )
    return _scheduler


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down")
    _scheduler = None


@asynccontextmanager
async def scheduler_lifespan(app):
    """FastAPI lifespan context manager that starts/stops the scheduler.

    Usage in ``main.py``::

        from app.tasks.scheduler import scheduler_lifespan

        app = FastAPI(lifespan=scheduler_lifespan)
    """
    start_scheduler()
    yield
    stop_scheduler()
