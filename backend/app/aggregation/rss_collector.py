"""RSS / Atom 采集器。"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from app.aggregation.base import BaseCollector, RawArticle
from app.models.source import Source

logger = logging.getLogger(__name__)

# httpx 默认超时（秒）
_DEFAULT_TIMEOUT = 30.0


class RSSCollector(BaseCollector):
    """RSS / Atom 采集器，使用 *feedparser* 解析订阅源。"""

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect(self, source: Source) -> list[RawArticle]:
        """从 RSS/Atom 源采集资讯。

        对于解析失败的单条 entry 会跳过并记录警告，不影响其余条目。
        """
        try:
            raw_xml = await self._fetch_feed(source.url)
        except Exception:
            logger.exception("Failed to fetch RSS feed: %s", source.url)
            return []

        feed = feedparser.parse(raw_xml)

        if feed.bozo and not feed.entries:
            logger.warning(
                "Feed at %s is malformed and contains no entries", source.url
            )
            return []

        articles: list[RawArticle] = []
        for entry in feed.entries:
            try:
                article = self._parse_entry(entry, source)
                if article is not None:
                    articles.append(article)
            except Exception:
                logger.warning(
                    "Skipping malformed feed entry in %s", source.url, exc_info=True
                )
        return articles

    async def validate_source(self, source: Source) -> bool:
        """检查 URL 是否返回有效的 RSS/Atom 内容。"""
        try:
            raw_xml = await self._fetch_feed(source.url)
            feed = feedparser.parse(raw_xml)
            # 至少能解析出 feed 版本或包含 entries 才算有效
            return bool(feed.version) or bool(feed.entries)
        except Exception:
            logger.debug("RSS validation failed for %s", source.url, exc_info=True)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_feed(self, url: str) -> str:
        """使用 httpx 异步获取 feed 内容。"""
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    @staticmethod
    def _parse_entry(entry: Any, source: Source) -> RawArticle | None:
        """将 feedparser entry 转换为 RawArticle。

        如果 entry 缺少标题或链接则返回 ``None``。
        """
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            return None

        excerpt = (
            entry.get("summary")
            or entry.get("description")
            or ""
        ).strip() or None

        published_at = _parse_date(entry)

        # feedparser 有时会在 entry 上标注语言
        language = (
            entry.get("language")
            or getattr(entry, "content", [{}])[0].get("language", "")
            if hasattr(entry, "content") and entry.content
            else ""
        ) or "en"

        return RawArticle(
            original_title=title,
            original_url=link,
            original_language=language,
            original_excerpt=excerpt,
            published_at=published_at,
            source_name=source.name,
        )


def _parse_date(entry: Any) -> datetime | None:
    """尝试从 feedparser entry 中解析发布时间。

    feedparser 会将日期解析为 ``time.struct_time`` 并存放在
    ``published_parsed`` / ``updated_parsed`` 中。如果这些字段不存在，
    则尝试用 ``email.utils.parsedate_to_datetime`` 解析原始字符串。
    """
    for attr in ("published_parsed", "updated_parsed"):
        struct = getattr(entry, attr, None)
        if struct is not None:
            try:
                dt = datetime(*struct[:6], tzinfo=timezone.utc)
                return dt
            except Exception:
                pass

    for attr in ("published", "updated"):
        raw = getattr(entry, attr, None)
        if raw:
            try:
                return parsedate_to_datetime(raw).replace(tzinfo=timezone.utc)
            except Exception:
                pass

    return None
