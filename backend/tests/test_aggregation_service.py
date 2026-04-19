"""Tests for the aggregation service — orchestration, dedup, storage, and error handling."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.aggregation.base import RawArticle
from app.models.source import Source
from app.services.aggregation_service import AggregationService


# ======================================================================
# Helpers
# ======================================================================


def _make_source(
    *,
    source_type: str = "rss",
    is_enabled: bool = True,
    name: str = "Test Source",
    url: str = "https://example.com/feed",
) -> MagicMock:
    """Create a mock Source ORM object."""
    source = MagicMock(spec=Source)
    source.id = uuid.uuid4()
    source.name = name
    source.url = url
    source.source_type = source_type
    source.is_enabled = is_enabled
    source.config = None
    source.last_collected_at = None
    source.last_collect_status = None
    source.last_error_message = None
    return source


def _make_raw_article(
    *,
    title: str = "Test Article",
    url: str = "https://example.com/article-1",
    language: str = "en",
) -> RawArticle:
    return RawArticle(
        original_title=title,
        original_url=url,
        original_language=language,
        original_excerpt="Some excerpt",
        published_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        source_name="Test Source",
    )


# ======================================================================
# AggregationService._get_collector
# ======================================================================


class TestGetCollector:
    def test_rss_collector(self):
        db = AsyncMock()
        service = AggregationService(db)
        collector = service._get_collector("rss")
        from app.aggregation.rss_collector import RSSCollector

        assert isinstance(collector, RSSCollector)

    def test_web_collector(self):
        db = AsyncMock()
        service = AggregationService(db)
        collector = service._get_collector("web")
        from app.aggregation.web_collector import WebCollector

        assert isinstance(collector, WebCollector)

    def test_unsupported_type_raises(self):
        db = AsyncMock()
        service = AggregationService(db)
        with pytest.raises(ValueError, match="Unsupported source type"):
            service._get_collector("twitter")


# ======================================================================
# AggregationService._build_article
# ======================================================================


class TestBuildArticle:
    def test_builds_article_with_correct_fields(self):
        source = _make_source()
        raw = _make_raw_article(title="Nike Air Max 2024", url="https://example.com/nike")

        article = AggregationService._build_article(raw, source)

        assert article.source_id == source.id
        assert article.original_title == "Nike Air Max 2024"
        assert article.original_url == "https://example.com/nike"
        assert article.original_language == "en"
        assert article.original_excerpt == "Some excerpt"
        assert article.published_at == datetime(2024, 1, 15, tzinfo=timezone.utc)
        assert article.processing_status == "pending"
        assert article.title_hash is not None
        assert len(article.title_hash) == 64  # SHA-256 hex

    def test_title_hash_is_deterministic(self):
        source = _make_source()
        raw = _make_raw_article(title="Same Title")

        a1 = AggregationService._build_article(raw, source)
        a2 = AggregationService._build_article(raw, source)

        assert a1.title_hash == a2.title_hash


# ======================================================================
# AggregationService._collect_from_source
# ======================================================================


class TestCollectFromSource:
    @pytest.mark.asyncio
    async def test_new_articles_stored(self):
        """Non-duplicate articles should be stored and returned."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(source_type="rss")
        raw_articles = [
            _make_raw_article(title="Article 1", url="https://example.com/1"),
            _make_raw_article(title="Article 2", url="https://example.com/2"),
        ]

        # Mock collector to return raw articles
        with patch.object(service._rss_collector, "collect", return_value=raw_articles):
            # Mock dedup to say nothing is duplicate
            with patch.object(service._dedup, "is_duplicate", return_value=False):
                result = await service._collect_from_source(source)

        assert result["collected"] == 2
        assert result["new"] == 2
        assert len(result["article_ids"]) == 2
        # db.add should have been called for each new article
        assert db.add.call_count == 2
        assert db.flush.call_count == 2

    @pytest.mark.asyncio
    async def test_duplicate_articles_skipped(self):
        """Duplicate articles should not be stored."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(source_type="rss")
        raw_articles = [
            _make_raw_article(title="Dup Article", url="https://example.com/dup"),
        ]

        with patch.object(service._rss_collector, "collect", return_value=raw_articles):
            with patch.object(service._dedup, "is_duplicate", return_value=True):
                result = await service._collect_from_source(source)

        assert result["collected"] == 1
        assert result["new"] == 0
        assert result["article_ids"] == []
        db.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_mixed_new_and_duplicate(self):
        """Mix of new and duplicate articles — only new ones stored."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(source_type="rss")
        raw_articles = [
            _make_raw_article(title="New", url="https://example.com/new"),
            _make_raw_article(title="Dup", url="https://example.com/dup"),
            _make_raw_article(title="Also New", url="https://example.com/also-new"),
        ]

        # First and third are new, second is duplicate
        with patch.object(service._rss_collector, "collect", return_value=raw_articles):
            with patch.object(
                service._dedup, "is_duplicate", side_effect=[False, True, False]
            ):
                result = await service._collect_from_source(source)

        assert result["collected"] == 3
        assert result["new"] == 2
        assert len(result["article_ids"]) == 2

    @pytest.mark.asyncio
    async def test_empty_collection(self):
        """Source returns no articles."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(source_type="rss")

        with patch.object(service._rss_collector, "collect", return_value=[]):
            result = await service._collect_from_source(source)

        assert result["collected"] == 0
        assert result["new"] == 0
        assert result["article_ids"] == []

    @pytest.mark.asyncio
    async def test_web_source_uses_web_collector(self):
        """Web source type should use the web collector."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(source_type="web")

        with patch.object(service._web_collector, "collect", return_value=[]) as mock_collect:
            await service._collect_from_source(source)

        mock_collect.assert_called_once_with(source)


# ======================================================================
# AggregationService.run_collection
# ======================================================================


class TestRunCollection:
    @pytest.mark.asyncio
    async def test_iterates_all_enabled_sources(self):
        """run_collection should process all enabled sources."""
        db = AsyncMock()
        service = AggregationService(db)

        sources = [
            _make_source(name="Source A"),
            _make_source(name="Source B"),
        ]

        # Mock the DB query to return our sources
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sources
        db.execute.return_value = mock_result

        with patch.object(
            service,
            "_collect_from_source",
            return_value={"collected": 5, "new": 3, "article_ids": ["id1", "id2", "id3"]},
        ) as mock_collect:
            summary = await service.run_collection()

        assert mock_collect.call_count == 2
        assert summary["sources_total"] == 2
        assert summary["sources_success"] == 2
        assert summary["sources_failed"] == 0
        assert summary["articles_collected"] == 10
        assert summary["articles_new"] == 6

    @pytest.mark.asyncio
    async def test_single_source_failure_does_not_affect_others(self):
        """If one source fails, others should still be processed."""
        db = AsyncMock()
        service = AggregationService(db)

        source_ok = _make_source(name="OK Source")
        source_fail = _make_source(name="Failing Source")
        sources = [source_fail, source_ok]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sources
        db.execute.return_value = mock_result

        async def _side_effect(source):
            if source.name == "Failing Source":
                raise RuntimeError("Connection refused")
            return {"collected": 3, "new": 2, "article_ids": ["a1", "a2"]}

        with patch.object(service, "_collect_from_source", side_effect=_side_effect):
            summary = await service.run_collection()

        assert summary["sources_total"] == 2
        assert summary["sources_success"] == 1
        assert summary["sources_failed"] == 1
        assert summary["articles_collected"] == 3
        assert summary["articles_new"] == 2
        assert len(summary["errors"]) == 1
        assert summary["errors"][0]["source_name"] == "Failing Source"

    @pytest.mark.asyncio
    async def test_source_status_updated_on_success(self):
        """Successful collection should update source status fields."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(name="Good Source")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [source]
        db.execute.return_value = mock_result

        with patch.object(
            service,
            "_collect_from_source",
            return_value={"collected": 1, "new": 1, "article_ids": ["x"]},
        ):
            await service.run_collection()

        assert source.last_collect_status == "success"
        assert source.last_error_message is None
        assert source.last_collected_at is not None

    @pytest.mark.asyncio
    async def test_source_status_updated_on_failure(self):
        """Failed collection should update source status with error info."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(name="Bad Source")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [source]
        db.execute.return_value = mock_result

        with patch.object(
            service,
            "_collect_from_source",
            side_effect=RuntimeError("Network error"),
        ):
            summary = await service.run_collection()

        assert source.last_collect_status == "error"
        assert "Network error" in source.last_error_message
        assert source.last_collected_at is not None
        assert summary["sources_failed"] == 1

    @pytest.mark.asyncio
    async def test_no_enabled_sources(self):
        """No enabled sources should return zero counts."""
        db = AsyncMock()
        service = AggregationService(db)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

        summary = await service.run_collection()

        assert summary["sources_total"] == 0
        assert summary["sources_success"] == 0
        assert summary["articles_new"] == 0


# ======================================================================
# AggregationService.collect_single_source
# ======================================================================


class TestCollectSingleSource:
    @pytest.mark.asyncio
    async def test_success(self):
        """Single source collection should return results and update status."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(name="Single Source")
        source_id = source.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = source
        db.execute.return_value = mock_result

        with patch.object(
            service,
            "_collect_from_source",
            return_value={"collected": 2, "new": 1, "article_ids": ["a1"]},
        ):
            result = await service.collect_single_source(source_id)

        assert result["collected"] == 2
        assert result["new"] == 1
        assert source.last_collect_status == "success"

    @pytest.mark.asyncio
    async def test_source_not_found(self):
        """Non-existent source should raise ValueError."""
        db = AsyncMock()
        service = AggregationService(db)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Source not found"):
            await service.collect_single_source(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_failure_updates_status_and_reraises(self):
        """Failed single source collection should update status and re-raise."""
        db = AsyncMock()
        service = AggregationService(db)

        source = _make_source(name="Failing Single")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = source
        db.execute.return_value = mock_result

        with patch.object(
            service,
            "_collect_from_source",
            side_effect=RuntimeError("Timeout"),
        ):
            with pytest.raises(RuntimeError, match="Timeout"):
                await service.collect_single_source(source.id)

        assert source.last_collect_status == "error"
        assert "Timeout" in source.last_error_message
