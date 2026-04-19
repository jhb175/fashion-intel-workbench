"""Tests for task 9.1 – Article schemas, ArticleService, and SearchService."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.article import (
    ArticleFiltersQuery,
    ArticleListItem,
    ArticleListResponse,
    ArticleResponse,
    ArticleTagResponse,
    TagItem,
    TagUpdateRequest,
)


# ======================================================================
# Schema tests
# ======================================================================


class TestArticleSchemas:
    """Verify Pydantic models for article endpoints."""

    def test_article_filters_defaults(self):
        q = ArticleFiltersQuery()
        assert q.page == 1
        assert q.page_size == 20
        assert q.brand is None
        assert q.keyword is None

    def test_article_filters_all_fields(self):
        q = ArticleFiltersQuery(
            page=2,
            page_size=10,
            brand="Nike",
            monitor_group="Sports",
            content_type="联名",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            keyword="球鞋",
            status="processed",
        )
        assert q.brand == "Nike"
        assert q.start_date == date(2024, 1, 1)
        assert q.status == "processed"

    def test_article_filters_page_min(self):
        with pytest.raises(PydanticValidationError):
            ArticleFiltersQuery(page=0)

    def test_article_filters_page_size_max(self):
        with pytest.raises(PydanticValidationError):
            ArticleFiltersQuery(page_size=101)

    def test_tag_item_valid_types(self):
        for t in ("brand", "monitor_group", "content_type", "keyword"):
            item = TagItem(tag_type=t, tag_value="test")
            assert item.tag_type == t

    def test_tag_item_invalid_type(self):
        with pytest.raises(PydanticValidationError):
            TagItem(tag_type="invalid", tag_value="test")

    def test_tag_item_empty_value_rejected(self):
        with pytest.raises(PydanticValidationError):
            TagItem(tag_type="brand", tag_value="")

    def test_tag_update_request_empty(self):
        req = TagUpdateRequest()
        assert req.add is None
        assert req.remove is None

    def test_tag_update_request_with_items(self):
        req = TagUpdateRequest(
            add=[TagItem(tag_type="brand", tag_value="Nike")],
            remove=[uuid.uuid4()],
        )
        assert len(req.add) == 1
        assert len(req.remove) == 1

    def test_article_response_model(self):
        now = datetime.now(timezone.utc)
        resp = ArticleResponse(
            id=uuid.uuid4(),
            source_id=uuid.uuid4(),
            original_title="Test Title",
            original_url="https://example.com/article",
            original_language="en",
            chinese_summary="测试摘要",
            published_at=now,
            collected_at=now,
            processing_status="processed",
            tags=[],
            is_bookmarked=True,
            is_topic_candidate=False,
            created_at=now,
            updated_at=now,
        )
        assert resp.is_bookmarked is True
        assert resp.processing_status == "processed"

    def test_article_list_response(self):
        resp = ArticleListResponse(items=[], total=0, page=1, page_size=20)
        assert resp.total == 0
        assert resp.items == []

    def test_article_tag_response(self):
        now = datetime.now(timezone.utc)
        tag = ArticleTagResponse(
            id=uuid.uuid4(),
            tag_type="brand",
            tag_value="Nike",
            is_auto=True,
            created_at=now,
        )
        assert tag.tag_type == "brand"


# ======================================================================
# SearchService unit tests (mock DB)
# ======================================================================


def _make_mock_tag(tag_type: str, tag_value: str) -> MagicMock:
    tag = MagicMock()
    tag.id = uuid.uuid4()
    tag.tag_type = tag_type
    tag.tag_value = tag_value
    tag.is_auto = True
    tag.created_at = datetime.now(timezone.utc)
    return tag


def _make_mock_article(
    *,
    published_at: datetime | None = None,
    processing_status: str = "processed",
    chinese_summary: str | None = "测试摘要",
    original_title: str = "Test Article",
    tags: list | None = None,
) -> MagicMock:
    article = MagicMock()
    article.id = uuid.uuid4()
    article.source_id = uuid.uuid4()
    article.original_title = original_title
    article.original_url = f"https://example.com/{uuid.uuid4()}"
    article.original_language = "en"
    article.original_excerpt = None
    article.chinese_summary = chinese_summary
    article.published_at = published_at or datetime.now(timezone.utc)
    article.collected_at = datetime.now(timezone.utc)
    article.processing_status = processing_status
    article.tags = tags or []
    article.created_at = datetime.now(timezone.utc)
    article.updated_at = datetime.now(timezone.utc)
    return article


class TestSearchServiceHelpers:
    """Test SearchService static/internal helpers."""

    def test_date_to_start_of_day(self):
        from app.services.search_service import SearchService

        d = date(2024, 6, 15)
        result = SearchService._date_to_start_of_day(d)
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.date() == d

    def test_date_to_end_of_day(self):
        from app.services.search_service import SearchService

        d = date(2024, 6, 15)
        result = SearchService._date_to_end_of_day(d)
        assert result.hour == 23
        assert result.minute == 59
        assert result.date() == d

    def test_tag_to_response(self):
        from app.services.search_service import SearchService

        tag = _make_mock_tag("brand", "Nike")
        resp = SearchService._tag_to_response(tag)
        assert resp.tag_type == "brand"
        assert resp.tag_value == "Nike"
        assert resp.is_auto is True


# ======================================================================
# ArticleService unit tests (mock DB)
# ======================================================================


class TestArticleServiceGetArticle:
    """Test ArticleService.get_article."""

    @pytest.mark.asyncio
    async def test_get_article_not_found(self):
        from app.services.article_service import ArticleService
        from app.utils.errors import NotFoundError

        db = AsyncMock()
        # Simulate no result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        service = ArticleService(db=db)
        with pytest.raises(NotFoundError, match="资讯不存在"):
            await service.get_article(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_article_success(self):
        from app.services.article_service import ArticleService

        article = _make_mock_article(
            tags=[_make_mock_tag("brand", "Nike")]
        )

        db = AsyncMock()
        # First call: get article; second/third: bookmark/topic check
        article_result = MagicMock()
        article_result.scalar_one_or_none.return_value = article

        no_result = MagicMock()
        no_result.scalar_one_or_none.return_value = None

        db.execute.side_effect = [article_result, no_result, no_result]

        service = ArticleService(db=db)
        user_id = uuid.uuid4()
        resp = await service.get_article(article.id, user_id=user_id)

        assert resp.id == article.id
        assert resp.is_bookmarked is False
        assert resp.is_topic_candidate is False
        assert len(resp.tags) == 1
        assert resp.tags[0].tag_value == "Nike"


class TestArticleServiceReprocess:
    """Test ArticleService.reprocess_article."""

    @pytest.mark.asyncio
    async def test_reprocess_resets_status(self):
        from app.services.article_service import ArticleService

        article = _make_mock_article(processing_status="failed")

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = article
        db.execute.return_value = mock_result

        service = ArticleService(db=db)
        resp = await service.reprocess_article(article.id)

        assert article.processing_status == "pending"

    @pytest.mark.asyncio
    async def test_reprocess_while_processing_raises(self):
        from app.services.article_service import ArticleService
        from app.utils.errors import ValidationError

        article = _make_mock_article(processing_status="processing")

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = article
        db.execute.return_value = mock_result

        service = ArticleService(db=db)
        with pytest.raises(ValidationError, match="正在处理中"):
            await service.reprocess_article(article.id)


class TestArticleServiceUpdateTags:
    """Test ArticleService.update_tags."""

    @pytest.mark.asyncio
    async def test_add_tag(self):
        from app.services.article_service import ArticleService

        article = _make_mock_article(tags=[])
        article_id = article.id

        db = AsyncMock()
        added_objects = []
        db.add = lambda obj: added_objects.append(obj)

        # First call: get article for update; second call: reload after update
        article_with_new_tag = _make_mock_article(
            tags=[_make_mock_tag("brand", "Nike")]
        )
        # Override id to match
        article_with_new_tag.id = article_id

        result1 = MagicMock()
        result1.scalar_one_or_none.return_value = article
        result2 = MagicMock()
        result2.scalar_one_or_none.return_value = article_with_new_tag

        db.execute.side_effect = [result1, result2]

        service = ArticleService(db=db)
        body = TagUpdateRequest(
            add=[TagItem(tag_type="brand", tag_value="Nike")]
        )
        tags = await service.update_tags(article_id, body)

        assert len(added_objects) == 1
        assert added_objects[0].tag_type == "brand"
        assert added_objects[0].tag_value == "Nike"
        assert added_objects[0].is_auto is False
        assert len(tags) == 1


# ======================================================================
# SearchService filter logic tests
# ======================================================================


class TestSearchServiceApplyTagFilter:
    """Test that _apply_tag_filter produces correct SQL sub-query structure."""

    def test_apply_tag_filter_returns_modified_stmt(self):
        from app.services.search_service import SearchService

        from sqlalchemy import select as sa_select
        from app.models.article import Article

        db = AsyncMock()
        service = SearchService(db=db)

        base_stmt = sa_select(Article)
        filtered_stmt = service._apply_tag_filter(base_stmt, "brand", "Nike")

        # The filtered statement should be different from the base
        assert str(filtered_stmt) != str(base_stmt)
        # The compiled SQL should reference article_tags
        compiled = str(filtered_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "article_tags" in compiled.lower()


class TestArticleFiltersQueryEdgeCases:
    """Edge cases for the filters query model."""

    def test_page_size_boundary_1(self):
        q = ArticleFiltersQuery(page_size=1)
        assert q.page_size == 1

    def test_page_size_boundary_100(self):
        q = ArticleFiltersQuery(page_size=100)
        assert q.page_size == 100

    def test_keyword_with_special_chars(self):
        q = ArticleFiltersQuery(keyword="Off-White™")
        assert q.keyword == "Off-White™"

    def test_empty_keyword_is_none(self):
        q = ArticleFiltersQuery(keyword=None)
        assert q.keyword is None
