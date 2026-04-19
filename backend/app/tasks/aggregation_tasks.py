"""Celery tasks for scheduled and on-demand article collection."""

from __future__ import annotations

import asyncio
import logging
import uuid

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.aggregation_tasks.run_scheduled_collection", bind=True)
def run_scheduled_collection(self) -> dict:
    """Celery task: run collection across all enabled sources.

    This is the entry point called by APScheduler on a periodic schedule.
    It creates its own DB session, runs the aggregation service, and
    triggers AI processing for each newly collected article.
    """
    logger.info("Starting scheduled collection run (task_id=%s)", self.request.id)

    async def _inner():
        from app.database import async_session_factory
        from app.services.aggregation_service import AggregationService

        async with async_session_factory() as db:
            service = AggregationService(db)
            summary = await service.run_collection()

        # Trigger AI processing for each new article
        article_ids: list[str] = []
        for error_entry in summary.get("errors", []):
            pass  # errors are already logged by the service

        # We need to collect article_ids from a second pass since
        # run_collection returns a flat summary. Re-query isn't needed
        # because we can trigger from the summary if we adjust the service.
        # For now, trigger a separate scan for pending articles.
        await _trigger_pending_ai_processing()

        return summary

    return _run_async(_inner())


@celery_app.task(name="app.tasks.aggregation_tasks.collect_source", bind=True)
def collect_source(self, source_id: str) -> dict:
    """Celery task: collect articles from a single source.

    Args:
        source_id: UUID string of the source to collect from.
    """
    logger.info(
        "Starting single-source collection (source_id=%s, task_id=%s)",
        source_id,
        self.request.id,
    )

    async def _inner():
        from app.database import async_session_factory
        from app.services.aggregation_service import AggregationService

        async with async_session_factory() as db:
            service = AggregationService(db)
            result = await service.collect_single_source(uuid.UUID(source_id))

        # Trigger AI processing for new articles
        for article_id in result.get("article_ids", []):
            from app.tasks.ai_tasks import process_article

            process_article.delay(article_id)

        return result

    return _run_async(_inner())


async def _trigger_pending_ai_processing() -> None:
    """Find all articles with processing_status='pending' and dispatch AI tasks."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.article import Article

    async with async_session_factory() as db:
        stmt = (
            select(Article.id)
            .where(Article.processing_status == "pending")
            .order_by(Article.created_at.asc())
        )
        result = await db.execute(stmt)
        article_ids = [str(row[0]) for row in result.all()]

    if article_ids:
        from app.tasks.ai_tasks import process_article

        for article_id in article_ids:
            process_article.delay(article_id)

        logger.info("Dispatched AI processing for %d pending articles", len(article_ids))
