"""Celery task for scheduled daily briefing generation."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.briefing_tasks.generate_daily_briefing_task", bind=True)
def generate_daily_briefing_task(self, briefing_date_iso: str | None = None) -> dict:
    """Generate the daily briefing for a given date (defaults to today UTC).

    This task is called by APScheduler on a daily schedule and can also be
    invoked manually via ``generate_daily_briefing_task.delay()``.
    """
    target_date = (
        date.fromisoformat(briefing_date_iso)
        if briefing_date_iso
        else datetime.now(timezone.utc).date()
    )
    logger.info(
        "Starting daily briefing generation for %s (task_id=%s)",
        target_date.isoformat(),
        self.request.id,
    )
    return _run_async(_generate_briefing_async(target_date))


async def _generate_briefing_async(target_date: date) -> dict:
    """Core async logic for generating a daily briefing."""
    from app.config import settings
    from app.database import async_session_factory
    from app.services.ai_provider_adapter import AIProviderAdapter
    from app.services.ai_service import AIService
    from app.services.briefing_service import BriefingService
    from app.services.encryption_service import EncryptionService

    async with async_session_factory() as db:
        try:
            encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
            adapter = AIProviderAdapter(encryption_service, db)
            ai_service = AIService(adapter)
            service = BriefingService(db=db, ai_service=ai_service)

            result = await service.generate_briefing(target_date)
            await db.commit()

            logger.info("Successfully generated briefing for %s", target_date.isoformat())
            return {
                "status": "success",
                "briefing_date": target_date.isoformat(),
                "briefing_id": str(result.id),
                "has_new_articles": result.has_new_articles,
            }
        except Exception as exc:
            logger.exception(
                "Failed to generate briefing for %s", target_date.isoformat()
            )
            return {
                "status": "failed",
                "briefing_date": target_date.isoformat(),
                "error": str(exc),
            }
