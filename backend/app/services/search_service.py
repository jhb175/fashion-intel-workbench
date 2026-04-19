"""Search service – multi-dimensional filtering + keyword full-text search."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import Select, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.bookmark import Bookmark, TopicCandidate
from app.models.tag import ArticleTag
from app.schemas.article import (
    ArticleFiltersQuery,
    ArticleListItem,
    ArticleListResponse,
    ArticleTagResponse,
)


class SearchService:
    """Multi-dimensional article search with keyword full-text support."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tag_to_response(tag: ArticleTag) -> ArticleTagResponse:
        return ArticleTagResponse(
            id=tag.id,
            tag_type=tag.tag_type,
            tag_value=tag.tag_value,
            is_auto=tag.is_auto,
            created_at=tag.created_at,
        )

    def _apply_tag_filter(
        self, stmt: Select, tag_type: str, tag_value: str
    ) -> Select:
        """Add a WHERE EXISTS sub-query that requires a matching tag."""
        subq = (
            select(ArticleTag.id)
            .where(
                ArticleTag.article_id == Article.id,
                ArticleTag.tag_type == tag_type,
                ArticleTag.tag_value == tag_value,
            )
            .correlate(Article)
            .exists()
        )
        return stmt.where(subq)

    @staticmethod
    def _date_to_start_of_day(d: date) -> datetime:
        return datetime.combine(d, time.min, tzinfo=timezone.utc)

    @staticmethod
    def _date_to_end_of_day(d: date) -> datetime:
        return datetime.combine(d, time.max, tzinfo=timezone.utc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_articles(
        self,
        filters: ArticleFiltersQuery,
        user_id: uuid.UUID | None = None,
    ) -> ArticleListResponse:
        """Execute a filtered, paginated article search.

        Filters combine with AND logic.  Keyword search uses PostgreSQL
        ``pg_trgm`` similarity via ``ILIKE`` on chinese_summary,
        original_title, and tag_value.
        """
        # Base query
        stmt: Select = (
            select(Article)
            .options(selectinload(Article.tags))
        )

        # --- Tag-based filters (brand / monitor_group / content_type) ---
        if filters.brand:
            stmt = self._apply_tag_filter(stmt, "brand", filters.brand)

        if filters.monitor_group:
            stmt = self._apply_tag_filter(stmt, "monitor_group", filters.monitor_group)

        if filters.content_type:
            stmt = self._apply_tag_filter(stmt, "content_type", filters.content_type)

        # --- Time range filter ---
        if filters.start_date:
            stmt = stmt.where(
                Article.published_at >= self._date_to_start_of_day(filters.start_date)
            )
        if filters.end_date:
            stmt = stmt.where(
                Article.published_at <= self._date_to_end_of_day(filters.end_date)
            )

        # --- Processing status filter ---
        if filters.status:
            stmt = stmt.where(Article.processing_status == filters.status)

        # --- Keyword full-text search (ILIKE / pg_trgm) ---
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            # Match in chinese_summary, original_title, or any tag_value
            tag_match_subq = (
                select(ArticleTag.id)
                .where(
                    ArticleTag.article_id == Article.id,
                    ArticleTag.tag_value.ilike(pattern),
                )
                .correlate(Article)
                .exists()
            )
            stmt = stmt.where(
                or_(
                    Article.chinese_summary.ilike(pattern),
                    Article.original_title.ilike(pattern),
                    tag_match_subq,
                )
            )

        # --- Count total before pagination ---
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        # --- Ordering + pagination ---
        stmt = (
            stmt.order_by(Article.published_at.desc().nullslast(), Article.collected_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        result = await self.db.execute(stmt)
        articles = result.scalars().unique().all()

        # --- Resolve bookmark / topic_candidate status per article ---
        article_ids = [a.id for a in articles]
        bookmarked_ids: set[uuid.UUID] = set()
        topic_ids: set[uuid.UUID] = set()

        if user_id and article_ids:
            bm_stmt = select(Bookmark.article_id).where(
                Bookmark.user_id == user_id,
                Bookmark.article_id.in_(article_ids),
            )
            tc_stmt = select(TopicCandidate.article_id).where(
                TopicCandidate.user_id == user_id,
                TopicCandidate.article_id.in_(article_ids),
            )
            bm_result = await self.db.execute(bm_stmt)
            tc_result = await self.db.execute(tc_stmt)
            bookmarked_ids = {row[0] for row in bm_result.all()}
            topic_ids = {row[0] for row in tc_result.all()}

        items = [
            ArticleListItem(
                id=a.id,
                original_title=a.original_title,
                original_url=a.original_url,
                original_language=a.original_language,
                chinese_summary=a.chinese_summary,
                published_at=a.published_at,
                collected_at=a.collected_at,
                processing_status=a.processing_status,
                tags=[self._tag_to_response(t) for t in a.tags],
                is_bookmarked=a.id in bookmarked_ids,
                is_topic_candidate=a.id in topic_ids,
            )
            for a in articles
        ]

        return ArticleListResponse(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )
