"""Bookmark and topic candidate service — add, remove, list with filtering."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.models.bookmark import Bookmark, TopicCandidate
from app.models.tag import ArticleTag
from app.schemas.bookmark import (
    BookmarkArticleBrief,
    BookmarkFiltersQuery,
    BookmarkListResponse,
    BookmarkResponse,
)
from app.utils.errors import ConflictError, NotFoundError


class BookmarkService:
    """Handles both bookmarks and topic candidates (similar logic)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Bookmarks
    # ------------------------------------------------------------------

    async def add_bookmark(self, user_id: uuid.UUID, article_id: uuid.UUID) -> BookmarkResponse:
        """Add a bookmark. Handles duplicate gracefully (idempotent)."""
        # Check article exists
        article = await self._get_article_or_raise(article_id)

        # Check for existing bookmark
        stmt = select(Bookmark).where(
            Bookmark.user_id == user_id,
            Bookmark.article_id == article_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            # Idempotent: return existing bookmark
            return self._to_response(existing, article)

        bookmark = Bookmark(user_id=user_id, article_id=article_id)
        self.db.add(bookmark)
        await self.db.flush()
        await self.db.refresh(bookmark)
        return self._to_response(bookmark, article)

    async def remove_bookmark(self, user_id: uuid.UUID, article_id: uuid.UUID) -> None:
        """Remove a bookmark by user_id + article_id."""
        stmt = delete(Bookmark).where(
            Bookmark.user_id == user_id,
            Bookmark.article_id == article_id,
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise NotFoundError("收藏记录不存在")

    async def list_bookmarks(
        self, user_id: uuid.UUID, filters: BookmarkFiltersQuery
    ) -> BookmarkListResponse:
        """List bookmarks with optional filtering and pagination."""
        return await self._list_items(
            model=Bookmark,
            user_id=user_id,
            filters=filters,
        )

    # ------------------------------------------------------------------
    # Topic candidates
    # ------------------------------------------------------------------

    async def add_topic_candidate(
        self, user_id: uuid.UUID, article_id: uuid.UUID
    ) -> BookmarkResponse:
        """Add a topic candidate. Handles duplicate gracefully (idempotent)."""
        article = await self._get_article_or_raise(article_id)

        stmt = select(TopicCandidate).where(
            TopicCandidate.user_id == user_id,
            TopicCandidate.article_id == article_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            return self._to_response(existing, article)

        candidate = TopicCandidate(user_id=user_id, article_id=article_id)
        self.db.add(candidate)
        await self.db.flush()
        await self.db.refresh(candidate)
        return self._to_response(candidate, article)

    async def remove_topic_candidate(self, user_id: uuid.UUID, article_id: uuid.UUID) -> None:
        """Remove a topic candidate by user_id + article_id."""
        stmt = delete(TopicCandidate).where(
            TopicCandidate.user_id == user_id,
            TopicCandidate.article_id == article_id,
        )
        result = await self.db.execute(stmt)
        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise NotFoundError("待选题记录不存在")

    async def list_topic_candidates(
        self, user_id: uuid.UUID, filters: BookmarkFiltersQuery
    ) -> BookmarkListResponse:
        """List topic candidates with optional filtering and pagination."""
        return await self._list_items(
            model=TopicCandidate,
            user_id=user_id,
            filters=filters,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_article_or_raise(self, article_id: uuid.UUID) -> Article:
        """Load an article or raise NotFoundError."""
        stmt = select(Article).where(Article.id == article_id)
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        if article is None:
            raise NotFoundError("资讯不存在")
        return article

    async def _list_items(
        self,
        model: type[Bookmark] | type[TopicCandidate],
        user_id: uuid.UUID,
        filters: BookmarkFiltersQuery,
    ) -> BookmarkListResponse:
        """Generic paginated list with optional brand/content_type/time filters.

        Filtering by brand or content_type requires joining through the article's
        tags (article_tags table).
        """
        # Base query
        base = select(model).where(model.user_id == user_id)

        # Join to Article for time filtering
        needs_article_join = filters.start_date is not None or filters.end_date is not None
        needs_tag_join = filters.brand is not None or filters.content_type is not None

        if needs_article_join or needs_tag_join:
            base = base.join(Article, model.article_id == Article.id)

        if needs_tag_join:
            base = base.join(ArticleTag, ArticleTag.article_id == Article.id)

        # Apply filters
        if filters.brand is not None:
            base = base.where(
                ArticleTag.tag_type == "brand",
                ArticleTag.tag_value == filters.brand,
            )

        if filters.content_type is not None:
            # If brand filter already applied, we need a second tag condition.
            # For simplicity, when both brand and content_type are specified we
            # require the article to have *both* tags (AND semantics).  We use
            # a subquery approach for the second filter.
            if filters.brand is not None:
                subq = (
                    select(ArticleTag.article_id)
                    .where(
                        ArticleTag.tag_type == "content_type",
                        ArticleTag.tag_value == filters.content_type,
                    )
                )
                base = base.where(Article.id.in_(subq))
            else:
                base = base.where(
                    ArticleTag.tag_type == "content_type",
                    ArticleTag.tag_value == filters.content_type,
                )

        if filters.start_date is not None:
            start_dt = datetime.combine(filters.start_date, time.min, tzinfo=timezone.utc)
            base = base.where(Article.published_at >= start_dt)

        if filters.end_date is not None:
            end_dt = datetime.combine(filters.end_date, time.max, tzinfo=timezone.utc)
            base = base.where(Article.published_at <= end_dt)

        # Ensure distinct results (joins may produce duplicates)
        base = base.distinct()

        # Count total
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Paginate
        offset = (filters.page - 1) * filters.page_size
        items_stmt = base.order_by(model.created_at.desc()).offset(offset).limit(filters.page_size)
        result = await self.db.execute(items_stmt)
        rows = list(result.scalars().all())

        # Build responses with nested article info
        items: list[BookmarkResponse] = []
        for row in rows:
            article = await self._get_article_or_raise(row.article_id)
            items.append(self._to_response(row, article))

        return BookmarkListResponse(
            items=items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    @staticmethod
    def _to_response(
        record: Bookmark | TopicCandidate,
        article: Article | None = None,
    ) -> BookmarkResponse:
        """Convert a Bookmark/TopicCandidate ORM object to a response model."""
        article_brief = None
        if article is not None:
            article_brief = BookmarkArticleBrief(
                id=article.id,
                original_title=article.original_title,
                original_url=article.original_url,
                original_language=article.original_language,
                chinese_summary=article.chinese_summary,
                published_at=article.published_at,
                processing_status=article.processing_status,
            )

        return BookmarkResponse(
            id=record.id,
            user_id=record.user_id,
            article_id=record.article_id,
            article=article_brief,
            created_at=record.created_at,
        )
