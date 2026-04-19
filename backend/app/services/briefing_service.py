"""Briefing service — generate, list, and retrieve daily briefings."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.briefing import BriefingArticle, DailyBriefing
from app.models.tag import ArticleTag
from app.schemas.briefing import (
    BriefingListItem,
    BriefingListResponse,
    BriefingResponse,
)
from app.services.ai_service import AIService, ArticleSummary
from app.utils.errors import NotFoundError

logger = logging.getLogger(__name__)


class BriefingService:
    """Handles daily briefing generation, listing, and retrieval."""

    def __init__(self, db: AsyncSession, ai_service: AIService | None = None) -> None:
        self.db = db
        self.ai_service = ai_service

    # ------------------------------------------------------------------
    # Generate briefing
    # ------------------------------------------------------------------

    async def generate_briefing(self, briefing_date: date) -> BriefingResponse:
        """Generate (or regenerate) a daily briefing for *briefing_date*.

        Steps:
        1. Load today's processed articles.
        2. Build ``ArticleSummary`` list for the AI service.
        3. Call ``AIService.generate_daily_briefing``.
        4. Upsert the ``DailyBriefing`` row (replace if one already exists
           for the same date).
        5. Store ``briefing_articles`` associations.
        """
        if self.ai_service is None:
            raise RuntimeError("AI service is required for briefing generation")

        # 1. Load articles for the date
        articles = await self._load_articles_for_date(briefing_date)

        has_new_articles = len(articles) > 0

        # 2. Build ArticleSummary list
        article_summaries = await self._build_article_summaries(articles)

        # 3. Call AI service
        briefing_content = await self.ai_service.generate_daily_briefing(
            article_summaries, briefing_date
        )

        # 4. Upsert DailyBriefing
        existing = await self._get_briefing_by_date(briefing_date)
        if existing is not None:
            # Update existing briefing
            existing.content = briefing_content.to_dict()
            existing.has_new_articles = has_new_articles
            briefing = existing
            # Remove old associations
            for ba in list(briefing.briefing_articles):
                await self.db.delete(ba)
            await self.db.flush()
        else:
            briefing = DailyBriefing(
                briefing_date=briefing_date,
                content=briefing_content.to_dict(),
                has_new_articles=has_new_articles,
            )
            self.db.add(briefing)
            await self.db.flush()
            await self.db.refresh(briefing)

        # 5. Store briefing_articles associations
        for article in articles:
            ba = BriefingArticle(
                briefing_id=briefing.id,
                article_id=article.id,
            )
            self.db.add(ba)

        await self.db.flush()
        await self.db.refresh(briefing)

        return self._to_response(briefing)

    # ------------------------------------------------------------------
    # List briefings
    # ------------------------------------------------------------------

    async def list_briefings(self, page: int = 1, page_size: int = 20) -> BriefingListResponse:
        """Return a paginated list of briefings ordered by date descending."""
        # Count total
        count_stmt = select(func.count()).select_from(DailyBriefing)
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Fetch page
        offset = (page - 1) * page_size
        stmt = (
            select(DailyBriefing)
            .order_by(DailyBriefing.briefing_date.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())

        items = [self._to_list_item(b) for b in rows]

        return BriefingListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # Get single briefing
    # ------------------------------------------------------------------

    async def get_briefing(self, briefing_id: uuid.UUID) -> BriefingResponse:
        """Return a single briefing by ID."""
        stmt = (
            select(DailyBriefing)
            .options(selectinload(DailyBriefing.briefing_articles))
            .where(DailyBriefing.id == briefing_id)
        )
        result = await self.db.execute(stmt)
        briefing = result.scalar_one_or_none()
        if briefing is None:
            raise NotFoundError("简报不存在")
        return self._to_response(briefing)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_articles_for_date(self, target_date: date) -> list[Article]:
        """Load all processed articles whose collected_at falls on *target_date*."""
        start_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(target_date, datetime.max.time(), tzinfo=timezone.utc)

        stmt = (
            select(Article)
            .options(selectinload(Article.tags))
            .where(
                Article.collected_at >= start_dt,
                Article.collected_at <= end_dt,
                Article.processing_status == "processed",
            )
            .order_by(Article.published_at.desc().nullslast())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _build_article_summaries(
        self, articles: list[Article]
    ) -> list[ArticleSummary]:
        """Convert ORM Article objects into lightweight ArticleSummary dataclasses."""
        summaries: list[ArticleSummary] = []
        for article in articles:
            # Determine monitor group from tags
            monitor_group = "其他"
            for tag in article.tags:
                if tag.tag_type == "monitor_group":
                    monitor_group = tag.tag_value
                    break

            summaries.append(
                ArticleSummary(
                    id=str(article.id),
                    title=article.original_title,
                    summary=article.chinese_summary or article.original_title,
                    monitor_group=monitor_group,
                )
            )
        return summaries

    async def _get_briefing_by_date(self, target_date: date) -> DailyBriefing | None:
        """Return the briefing for a specific date, or None."""
        stmt = (
            select(DailyBriefing)
            .options(selectinload(DailyBriefing.briefing_articles))
            .where(DailyBriefing.briefing_date == target_date)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _to_response(briefing: DailyBriefing) -> BriefingResponse:
        return BriefingResponse(
            id=briefing.id,
            briefing_date=briefing.briefing_date,
            content=briefing.content,
            has_new_articles=briefing.has_new_articles,
            created_at=briefing.created_at,
        )

    @staticmethod
    def _to_list_item(briefing: DailyBriefing) -> BriefingListItem:
        # Extract summary from JSONB content for the list view
        summary = ""
        if isinstance(briefing.content, dict):
            summary = briefing.content.get("summary", "")

        return BriefingListItem(
            id=briefing.id,
            briefing_date=briefing.briefing_date,
            has_new_articles=briefing.has_new_articles,
            summary=summary,
            created_at=briefing.created_at,
        )
