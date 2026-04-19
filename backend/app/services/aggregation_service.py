"""Aggregation service — orchestrates collection from all enabled sources."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.aggregation.base import RawArticle
from app.aggregation.dedup import DeduplicationService
from app.aggregation.rss_collector import RSSCollector
from app.aggregation.web_collector import WebCollector
from app.models.article import Article
from app.models.source import Source

logger = logging.getLogger(__name__)


class AggregationService:
    """Aggregation scheduling logic.

    Iterates all enabled sources, calls the appropriate collector,
    deduplicates each article, stores new articles in the DB, and
    triggers AI processing for each new article.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._dedup = DeduplicationService(db)
        self._rss_collector = RSSCollector()
        self._web_collector = WebCollector()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_collection(self) -> dict:
        """Run collection across **all** enabled sources.

        Returns a summary dict with counts of sources processed, articles
        collected, new articles stored, and any errors encountered.

        A single source failure does **not** affect other sources.
        """
        stmt = select(Source).where(Source.is_enabled.is_(True))
        result = await self._db.execute(stmt)
        sources = list(result.scalars().all())

        summary = {
            "sources_total": len(sources),
            "sources_success": 0,
            "sources_failed": 0,
            "articles_collected": 0,
            "articles_new": 0,
            "errors": [],
        }

        for source in sources:
            try:
                source_result = await self._collect_from_source(source)
                summary["articles_collected"] += source_result["collected"]
                summary["articles_new"] += source_result["new"]
                summary["sources_success"] += 1

                # Update source status on success
                source.last_collected_at = datetime.now(timezone.utc)
                source.last_collect_status = "success"
                source.last_error_message = None

            except Exception as exc:
                logger.exception(
                    "Collection failed for source %s (%s)", source.name, source.id
                )
                summary["sources_failed"] += 1
                summary["errors"].append(
                    {"source_id": str(source.id), "source_name": source.name, "error": str(exc)}
                )

                # Update source status on failure
                source.last_collected_at = datetime.now(timezone.utc)
                source.last_collect_status = "error"
                source.last_error_message = str(exc)[:500]

        await self._db.commit()

        logger.info(
            "Collection run complete: %d sources, %d success, %d failed, %d new articles",
            summary["sources_total"],
            summary["sources_success"],
            summary["sources_failed"],
            summary["articles_new"],
        )
        return summary

    async def collect_single_source(self, source_id: uuid.UUID) -> dict:
        """Collect from a single source by ID.

        Returns a summary dict for the single source.
        """
        stmt = select(Source).where(Source.id == source_id)
        result = await self._db.execute(stmt)
        source = result.scalar_one_or_none()

        if source is None:
            raise ValueError(f"Source not found: {source_id}")

        try:
            source_result = await self._collect_from_source(source)
            source.last_collected_at = datetime.now(timezone.utc)
            source.last_collect_status = "success"
            source.last_error_message = None
            await self._db.commit()
            return source_result

        except Exception as exc:
            logger.exception(
                "Collection failed for source %s (%s)", source.name, source.id
            )
            source.last_collected_at = datetime.now(timezone.utc)
            source.last_collect_status = "error"
            source.last_error_message = str(exc)[:500]
            await self._db.commit()
            raise

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _collect_from_source(self, source: Source) -> dict:
        """Collect articles from a single source, dedup, and store.

        Returns ``{"collected": int, "new": int, "article_ids": list[str]}``.
        """
        collector = self._get_collector(source.source_type)
        raw_articles = await collector.collect(source)

        new_article_ids: list[str] = []
        for raw in raw_articles:
            if await self._dedup.is_duplicate(raw):
                continue

            article = self._build_article(raw, source)
            self._db.add(article)
            # Flush so the article gets an ID and is visible to subsequent
            # dedup checks within the same batch.
            await self._db.flush()
            new_article_ids.append(str(article.id))

        return {
            "collected": len(raw_articles),
            "new": len(new_article_ids),
            "article_ids": new_article_ids,
        }

    def _get_collector(self, source_type: str):
        """Return the appropriate collector for the source type."""
        if source_type == "rss":
            return self._rss_collector
        if source_type == "web":
            return self._web_collector
        raise ValueError(f"Unsupported source type: {source_type}")

    @staticmethod
    def _build_article(raw: RawArticle, source: Source) -> Article:
        """Convert a ``RawArticle`` into an ``Article`` ORM instance."""
        title_hash = DeduplicationService.compute_title_hash(raw.original_title)
        return Article(
            source_id=source.id,
            original_title=raw.original_title,
            original_url=raw.original_url,
            original_language=raw.original_language,
            original_excerpt=raw.original_excerpt,
            published_at=raw.published_at,
            processing_status="pending",
            title_hash=title_hash,
        )
