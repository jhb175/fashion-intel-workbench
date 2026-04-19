"""Tests for the aggregation module: collectors and deduplication service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.aggregation.base import RawArticle
from app.aggregation.dedup import DeduplicationService, _normalize_title
from app.aggregation.rss_collector import RSSCollector, _parse_date
from app.aggregation.web_collector import WebCollector


# ======================================================================
# RawArticle dataclass
# ======================================================================


class TestRawArticle:
    def test_defaults(self):
        article = RawArticle(original_title="Test", original_url="https://example.com")
        assert article.original_language == "en"
        assert article.original_excerpt is None
        assert article.published_at is None
        assert article.source_name == ""

    def test_all_fields(self):
        now = datetime.now(tz=timezone.utc)
        article = RawArticle(
            original_title="Title",
            original_url="https://example.com/article",
            original_language="zh",
            original_excerpt="Excerpt text",
            published_at=now,
            source_name="Test Source",
        )
        assert article.original_title == "Title"
        assert article.original_language == "zh"
        assert article.published_at == now


# ======================================================================
# Title normalization
# ======================================================================


class TestNormalizeTitle:
    def test_lowercase(self):
        assert _normalize_title("HELLO WORLD") == "hello world"

    def test_strip_punctuation(self):
        assert _normalize_title("Hello, World!") == "hello world"

    def test_collapse_whitespace(self):
        assert _normalize_title("  hello   world  ") == "hello world"

    def test_unicode_normalization(self):
        # NFKC normalizes ﬁ → fi
        assert _normalize_title("ﬁne") == "fine"

    def test_empty_string(self):
        assert _normalize_title("") == ""


# ======================================================================
# DeduplicationService — title similarity
# ======================================================================


class TestTitleSimilarity:
    def test_identical_titles(self):
        sim = DeduplicationService.compute_title_similarity("Hello World", "Hello World")
        assert sim == 1.0

    def test_completely_different(self):
        sim = DeduplicationService.compute_title_similarity("abc", "xyz")
        assert sim < 0.5

    def test_similar_titles(self):
        sim = DeduplicationService.compute_title_similarity(
            "Nike Launches New Air Max 2024",
            "Nike Launches New Air Max 2024 Edition",
        )
        assert sim >= 0.85

    def test_case_insensitive(self):
        sim = DeduplicationService.compute_title_similarity("Hello", "hello")
        assert sim == 1.0

    def test_punctuation_ignored(self):
        sim = DeduplicationService.compute_title_similarity(
            "Hello, World!", "Hello World"
        )
        assert sim == 1.0

    def test_both_empty(self):
        sim = DeduplicationService.compute_title_similarity("", "")
        assert sim == 1.0

    def test_one_empty(self):
        sim = DeduplicationService.compute_title_similarity("Hello", "")
        assert sim == 0.0

    def test_symmetry(self):
        a = "Nike Air Max 2024 Release"
        b = "Nike Air Max 2024 Launch"
        sim_ab = DeduplicationService.compute_title_similarity(a, b)
        sim_ba = DeduplicationService.compute_title_similarity(b, a)
        assert sim_ab == sim_ba


# ======================================================================
# DeduplicationService — title hash
# ======================================================================


class TestTitleHash:
    def test_deterministic(self):
        h1 = DeduplicationService.compute_title_hash("Hello World")
        h2 = DeduplicationService.compute_title_hash("Hello World")
        assert h1 == h2

    def test_case_insensitive(self):
        h1 = DeduplicationService.compute_title_hash("Hello World")
        h2 = DeduplicationService.compute_title_hash("hello world")
        assert h1 == h2

    def test_different_titles_different_hashes(self):
        h1 = DeduplicationService.compute_title_hash("Title A")
        h2 = DeduplicationService.compute_title_hash("Title B")
        assert h1 != h2

    def test_hash_length(self):
        h = DeduplicationService.compute_title_hash("Test")
        assert len(h) == 64  # SHA-256 hex digest


# ======================================================================
# DeduplicationService — is_duplicate (with mocked DB)
# ======================================================================


class TestIsDuplicate:
    @pytest.fixture()
    def mock_db(self):
        db = AsyncMock()
        return db

    @pytest.fixture()
    def service(self, mock_db):
        return DeduplicationService(mock_db)

    @pytest.fixture()
    def sample_article(self):
        return RawArticle(
            original_title="Nike Launches New Shoe",
            original_url="https://example.com/nike-shoe",
            source_name="Test",
        )

    @pytest.mark.asyncio
    async def test_duplicate_by_url(self, service, mock_db, sample_article):
        """URL 精确匹配应判定为重复。"""
        # Mock _url_exists to return True
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid.uuid4()
        mock_db.execute.return_value = mock_result

        assert await service.is_duplicate(sample_article) is True

    @pytest.mark.asyncio
    async def test_not_duplicate(self, service, mock_db, sample_article):
        """URL 不存在、hash 不存在、标题不相似 → 非重复。"""
        # All DB queries return None / empty
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None

        mock_result_empty = MagicMock()
        mock_result_empty.all.return_value = []

        mock_db.execute.side_effect = [
            mock_result_none,  # _url_exists
            mock_result_none,  # _title_hash_exists
            mock_result_empty,  # _get_recent_titles
        ]

        assert await service.is_duplicate(sample_article) is False

    @pytest.mark.asyncio
    async def test_duplicate_by_title_hash(self, service, mock_db, sample_article):
        """Title hash 精确匹配应判定为重复。"""
        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None

        mock_result_found = MagicMock()
        mock_result_found.scalar_one_or_none.return_value = uuid.uuid4()

        mock_db.execute.side_effect = [
            mock_result_none,   # _url_exists → not found
            mock_result_found,  # _title_hash_exists → found
        ]

        assert await service.is_duplicate(sample_article) is True

    @pytest.mark.asyncio
    async def test_duplicate_by_similar_title(self, service, mock_db):
        """标题相似度超过阈值应判定为重复。"""
        article = RawArticle(
            original_title="Nike Launches New Air Max 2024 Edition",
            original_url="https://example.com/new-url",
            source_name="Test",
        )

        mock_result_none = MagicMock()
        mock_result_none.scalar_one_or_none.return_value = None

        mock_result_titles = MagicMock()
        mock_result_titles.all.return_value = [
            ("Nike Launches New Air Max 2024",),
        ]

        mock_db.execute.side_effect = [
            mock_result_none,    # _url_exists
            mock_result_none,    # _title_hash_exists
            mock_result_titles,  # _get_recent_titles
        ]

        assert await service.is_duplicate(article) is True


# ======================================================================
# RSSCollector
# ======================================================================


class TestRSSCollector:
    @pytest.fixture()
    def collector(self):
        return RSSCollector(timeout=10.0)

    @pytest.fixture()
    def mock_source(self):
        source = MagicMock()
        source.name = "Test RSS"
        source.url = "https://example.com/feed.xml"
        return source

    @pytest.mark.asyncio
    async def test_collect_valid_feed(self, collector, mock_source):
        """Valid RSS feed should return parsed articles."""
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <title>Test Feed</title>
            <item>
              <title>Article One</title>
              <link>https://example.com/article-1</link>
              <description>First article summary</description>
              <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
            </item>
            <item>
              <title>Article Two</title>
              <link>https://example.com/article-2</link>
              <description>Second article summary</description>
            </item>
          </channel>
        </rss>"""

        with patch.object(collector, "_fetch_feed", return_value=rss_xml):
            articles = await collector.collect(mock_source)

        assert len(articles) == 2
        assert articles[0].original_title == "Article One"
        assert articles[0].original_url == "https://example.com/article-1"
        assert articles[0].original_excerpt == "First article summary"
        assert articles[0].source_name == "Test RSS"
        assert articles[0].published_at is not None

    @pytest.mark.asyncio
    async def test_collect_skips_entries_without_title(self, collector, mock_source):
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <link>https://example.com/no-title</link>
            </item>
            <item>
              <title>Has Title</title>
              <link>https://example.com/has-title</link>
            </item>
          </channel>
        </rss>"""

        with patch.object(collector, "_fetch_feed", return_value=rss_xml):
            articles = await collector.collect(mock_source)

        assert len(articles) == 1
        assert articles[0].original_title == "Has Title"

    @pytest.mark.asyncio
    async def test_collect_returns_empty_on_fetch_error(self, collector, mock_source):
        with patch.object(
            collector, "_fetch_feed", side_effect=httpx.HTTPError("timeout")
        ):
            articles = await collector.collect(mock_source)

        assert articles == []

    @pytest.mark.asyncio
    async def test_validate_source_valid(self, collector, mock_source):
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel><title>Test</title></channel>
        </rss>"""

        with patch.object(collector, "_fetch_feed", return_value=rss_xml):
            assert await collector.validate_source(mock_source) is True

    @pytest.mark.asyncio
    async def test_validate_source_invalid(self, collector, mock_source):
        with patch.object(
            collector, "_fetch_feed", side_effect=httpx.HTTPError("fail")
        ):
            assert await collector.validate_source(mock_source) is False


# ======================================================================
# RSSCollector — date parsing
# ======================================================================


class TestParseDateHelper:
    def test_published_parsed(self):
        """feedparser struct_time in published_parsed."""
        entry = MagicMock()
        entry.published_parsed = (2024, 1, 15, 10, 30, 0, 0, 15, 0)
        entry.updated_parsed = None
        entry.published = None
        entry.updated = None
        dt = _parse_date(entry)
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_rfc2822_string(self):
        entry = MagicMock()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = "Mon, 15 Jan 2024 10:30:00 +0000"
        entry.updated = None
        dt = _parse_date(entry)
        assert dt is not None
        assert dt.year == 2024

    def test_no_date(self):
        entry = MagicMock()
        entry.published_parsed = None
        entry.updated_parsed = None
        entry.published = None
        entry.updated = None
        assert _parse_date(entry) is None


# ======================================================================
# WebCollector
# ======================================================================


class TestWebCollector:
    @pytest.fixture()
    def collector(self):
        return WebCollector(timeout=10.0)

    @pytest.fixture()
    def mock_source(self):
        source = MagicMock()
        source.name = "Test Web"
        source.url = "https://example.com/news"
        source.config = {
            "article_selector": "div.article",
            "title_selector": "h2 a",
            "link_selector": "h2 a",
            "excerpt_selector": "p.summary",
        }
        return source

    @pytest.mark.asyncio
    async def test_collect_valid_page(self, collector, mock_source):
        html = """
        <html><body>
          <div class="article">
            <h2><a href="/news/1">Article One</a></h2>
            <p class="summary">Summary one</p>
          </div>
          <div class="article">
            <h2><a href="https://example.com/news/2">Article Two</a></h2>
            <p class="summary">Summary two</p>
          </div>
        </body></html>
        """

        with patch.object(collector, "_fetch_page", return_value=html):
            articles = await collector.collect(mock_source)

        assert len(articles) == 2
        assert articles[0].original_title == "Article One"
        # Relative URL should be resolved
        assert articles[0].original_url == "https://example.com/news/1"
        assert articles[0].original_excerpt == "Summary one"
        assert articles[1].original_url == "https://example.com/news/2"

    @pytest.mark.asyncio
    async def test_collect_missing_config(self, collector, mock_source):
        mock_source.config = {}
        articles = await collector.collect(mock_source)
        assert articles == []

    @pytest.mark.asyncio
    async def test_collect_skips_entries_without_link(self, collector, mock_source):
        html = """
        <html><body>
          <div class="article">
            <h2><a href="">No Link</a></h2>
          </div>
          <div class="article">
            <h2><a href="/news/ok">Has Link</a></h2>
          </div>
        </body></html>
        """

        with patch.object(collector, "_fetch_page", return_value=html):
            articles = await collector.collect(mock_source)

        assert len(articles) == 1
        assert articles[0].original_title == "Has Link"

    @pytest.mark.asyncio
    async def test_collect_returns_empty_on_fetch_error(self, collector, mock_source):
        with patch.object(
            collector, "_fetch_page", side_effect=httpx.HTTPError("timeout")
        ):
            articles = await collector.collect(mock_source)
        assert articles == []

    @pytest.mark.asyncio
    async def test_validate_source_valid(self, collector, mock_source):
        with patch.object(collector, "_fetch_page", return_value="<html>content</html>"):
            assert await collector.validate_source(mock_source) is True

    @pytest.mark.asyncio
    async def test_validate_source_invalid(self, collector, mock_source):
        with patch.object(
            collector, "_fetch_page", side_effect=httpx.HTTPError("fail")
        ):
            assert await collector.validate_source(mock_source) is False

    @pytest.mark.asyncio
    async def test_collect_without_excerpt_selector(self, collector, mock_source):
        mock_source.config = {
            "article_selector": "div.article",
            "title_selector": "h2 a",
            "link_selector": "h2 a",
        }
        html = """
        <html><body>
          <div class="article">
            <h2><a href="/news/1">Title</a></h2>
          </div>
        </body></html>
        """

        with patch.object(collector, "_fetch_page", return_value=html):
            articles = await collector.collect(mock_source)

        assert len(articles) == 1
        assert articles[0].original_excerpt is None
