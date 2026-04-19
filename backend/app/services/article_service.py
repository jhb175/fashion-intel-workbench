"""Article service – single article retrieval, tag editing, status management."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.bookmark import Bookmark, TopicCandidate
from app.models.tag import ArticleTag
from app.schemas.article import (
    ArticleResponse,
    ArticleTagResponse,
    TagItem,
    TagUpdateRequest,
)
from app.utils.errors import NotFoundError, ValidationError


class ArticleService:
    """Business logic for single-article operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_article_or_404(self, article_id: uuid.UUID) -> Article:
        """Fetch an article with eagerly-loaded tags or raise ``NotFoundError``."""
        stmt = (
            select(Article)
            .options(selectinload(Article.tags))
            .where(Article.id == article_id)
        )
        result = await self.db.execute(stmt)
        article = result.scalar_one_or_none()
        if article is None:
            raise NotFoundError("资讯不存在")
        return article

    @staticmethod
    def _tag_to_response(tag: ArticleTag) -> ArticleTagResponse:
        return ArticleTagResponse(
            id=tag.id,
            tag_type=tag.tag_type,
            tag_value=tag.tag_value,
            is_auto=tag.is_auto,
            created_at=tag.created_at,
        )

    async def _check_user_marks(
        self, article_id: uuid.UUID, user_id: uuid.UUID | None
    ) -> tuple[bool, bool]:
        """Return (is_bookmarked, is_topic_candidate) for a user."""
        if user_id is None:
            return False, False

        bm_stmt = select(Bookmark.id).where(
            Bookmark.article_id == article_id,
            Bookmark.user_id == user_id,
        )
        tc_stmt = select(TopicCandidate.id).where(
            TopicCandidate.article_id == article_id,
            TopicCandidate.user_id == user_id,
        )
        bm_result = await self.db.execute(bm_stmt)
        tc_result = await self.db.execute(tc_stmt)
        return bm_result.scalar_one_or_none() is not None, tc_result.scalar_one_or_none() is not None

    def _article_to_response(
        self,
        article: Article,
        is_bookmarked: bool = False,
        is_topic_candidate: bool = False,
    ) -> ArticleResponse:
        return ArticleResponse(
            id=article.id,
            source_id=article.source_id,
            original_title=article.original_title,
            original_url=article.original_url,
            original_language=article.original_language,
            original_excerpt=article.original_excerpt,
            chinese_summary=article.chinese_summary,
            published_at=article.published_at,
            collected_at=article.collected_at,
            processing_status=article.processing_status,
            tags=[self._tag_to_response(t) for t in article.tags],
            is_bookmarked=is_bookmarked,
            is_topic_candidate=is_topic_candidate,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    # ------------------------------------------------------------------
    # Get single article
    # ------------------------------------------------------------------

    async def get_article(
        self, article_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> ArticleResponse:
        """Return a single article with tags and bookmark/topic status."""
        article = await self._get_article_or_404(article_id)
        is_bm, is_tc = await self._check_user_marks(article_id, user_id)
        return self._article_to_response(article, is_bm, is_tc)

    # ------------------------------------------------------------------
    # Tag editing
    # ------------------------------------------------------------------

    async def update_tags(
        self, article_id: uuid.UUID, body: TagUpdateRequest
    ) -> list[ArticleTagResponse]:
        """Add and/or remove tags on an article. Returns the updated tag list."""
        article = await self._get_article_or_404(article_id)

        # Remove tags
        if body.remove:
            for tag_id in body.remove:
                tag_stmt = select(ArticleTag).where(
                    ArticleTag.id == tag_id,
                    ArticleTag.article_id == article_id,
                )
                result = await self.db.execute(tag_stmt)
                tag = result.scalar_one_or_none()
                if tag is not None:
                    await self.db.delete(tag)

        # Add tags
        if body.add:
            for item in body.add:
                new_tag = ArticleTag(
                    article_id=article_id,
                    tag_type=item.tag_type,
                    tag_value=item.tag_value,
                    is_auto=False,
                )
                self.db.add(new_tag)

        await self.db.flush()

        # Reload tags
        refreshed = await self._get_article_or_404(article_id)
        return [self._tag_to_response(t) for t in refreshed.tags]

    # ------------------------------------------------------------------
    # Reprocess (trigger AI reprocessing)
    # ------------------------------------------------------------------

    async def reprocess_article(self, article_id: uuid.UUID) -> ArticleResponse:
        """Reset processing status to 'pending' so the AI pipeline re-processes it."""
        article = await self._get_article_or_404(article_id)
        if article.processing_status == "processing":
            raise ValidationError("资讯正在处理中，请稍后再试")
        article.processing_status = "pending"
        await self.db.flush()
        await self.db.refresh(article)
        return self._article_to_response(article)
