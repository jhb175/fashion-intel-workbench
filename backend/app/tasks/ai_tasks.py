"""Celery tasks for asynchronous AI analysis (summary generation + tag extraction)."""

from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.ai_tasks.process_article", bind=True)
def process_article(self, article_id: str) -> dict:
    """Process a single article through the AI pipeline.

    Steps:
    1. Load the article from DB
    2. Call ai_service.generate_summary() to create a Chinese summary
    3. Call ai_service.extract_tags() to extract and store tags
    4. Update article.processing_status to "processed"
    5. On error: set processing_status to "failed"
    """
    logger.info(
        "Starting AI processing for article %s (task_id=%s)",
        article_id,
        self.request.id,
    )
    return _run_async(_process_article_async(article_id))


@celery_app.task(name="app.tasks.ai_tasks.reprocess_article", bind=True)
def reprocess_article(self, article_id: str) -> dict:
    """Reprocess an article — resets status first, then runs the full pipeline."""
    logger.info(
        "Starting AI reprocessing for article %s (task_id=%s)",
        article_id,
        self.request.id,
    )
    return _run_async(_reprocess_article_async(article_id))


# ---------------------------------------------------------------------------
# Async implementation
# ---------------------------------------------------------------------------


async def _process_article_async(article_id: str) -> dict:
    """Core async logic for processing a single article."""
    from sqlalchemy import select

    from app.config import settings
    from app.database import async_session_factory
    from app.models.article import Article
    from app.models.brand import Brand
    from app.models.keyword import Keyword
    from app.models.tag import ArticleTag
    from app.services.ai_provider_adapter import AIProviderAdapter
    from app.services.ai_service import AIService
    from app.services.encryption_service import EncryptionService

    async with async_session_factory() as db:
        # 1. Load article
        stmt = select(Article).where(Article.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if article is None:
            logger.warning("Article not found: %s", article_id)
            return {"status": "not_found", "article_id": article_id}

        # Mark as processing
        article.processing_status = "processing"
        await db.commit()

        try:
            # Build AI service
            encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
            adapter = AIProviderAdapter(encryption_service, db)
            ai_service = AIService(adapter)

            # 2. Generate Chinese summary
            content = article.original_excerpt or article.original_title
            summary = await ai_service.generate_summary(
                title=article.original_title,
                content=content,
                source_lang=article.original_language,
            )
            article.chinese_summary = summary

            # 3. Extract tags — load brand pool and keyword pool from DB
            brand_pool = await _load_brand_pool(db)
            keyword_pool = await _load_keyword_pool(db)

            tags = await ai_service.extract_tags(
                title=article.original_title,
                content=content,
                brand_pool=brand_pool,
                keyword_pool=keyword_pool,
            )

            # Store tags in DB
            await _store_tags(db, article.id, tags)

            # 4. Mark as processed
            article.processing_status = "processed"
            await db.commit()

            logger.info("Successfully processed article %s", article_id)
            return {"status": "processed", "article_id": article_id}

        except Exception as exc:
            logger.exception("AI processing failed for article %s", article_id)
            # 5. On error: set status to failed
            article.processing_status = "failed"
            await db.commit()
            return {"status": "failed", "article_id": article_id, "error": str(exc)}


async def _reprocess_article_async(article_id: str) -> dict:
    """Reset article status and re-run the full AI pipeline."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.article import Article
    from app.models.tag import ArticleTag

    async with async_session_factory() as db:
        # Reset status
        stmt = select(Article).where(Article.id == article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if article is None:
            logger.warning("Article not found for reprocessing: %s", article_id)
            return {"status": "not_found", "article_id": article_id}

        # Remove existing auto-generated tags
        from sqlalchemy import delete

        await db.execute(
            delete(ArticleTag).where(
                ArticleTag.article_id == article.id,
                ArticleTag.is_auto.is_(True),
            )
        )

        # Reset status to pending
        article.processing_status = "pending"
        article.chinese_summary = None
        await db.commit()

    # Now run the standard processing pipeline
    return await _process_article_async(article_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _load_brand_pool(db) -> list[str]:
    """Load all brand names (English) from the database."""
    from sqlalchemy import select

    from app.models.brand import Brand

    stmt = select(Brand.name_en)
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def _load_keyword_pool(db) -> list[str]:
    """Load all keywords (English) from the database."""
    from sqlalchemy import select

    from app.models.keyword import Keyword

    stmt = select(Keyword.word_en)
    result = await db.execute(stmt)
    return [row[0] for row in result.all()]


async def _store_tags(db, article_id, tags) -> None:
    """Store extracted tags as ArticleTag records."""
    from app.models.tag import ArticleTag

    tag_records = []

    for brand in tags.brands:
        tag_records.append(
            ArticleTag(
                article_id=article_id,
                tag_type="brand",
                tag_value=brand,
                is_auto=True,
            )
        )

    for group in tags.monitor_groups:
        tag_records.append(
            ArticleTag(
                article_id=article_id,
                tag_type="monitor_group",
                tag_value=group,
                is_auto=True,
            )
        )

    for content_type in tags.content_types:
        tag_records.append(
            ArticleTag(
                article_id=article_id,
                tag_type="content_type",
                tag_value=content_type,
                is_auto=True,
            )
        )

    for keyword in tags.keywords:
        tag_records.append(
            ArticleTag(
                article_id=article_id,
                tag_type="keyword",
                tag_value=keyword,
                is_auto=True,
            )
        )

    for record in tag_records:
        db.add(record)

    await db.flush()
