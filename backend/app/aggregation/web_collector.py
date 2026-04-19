"""网页采集器 — 使用 httpx + BeautifulSoup4 从公开网页提取资讯。"""

from __future__ import annotations

import logging
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.aggregation.base import BaseCollector, RawArticle
from app.models.source import Source

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0


class WebCollector(BaseCollector):
    """网页采集器。

    资讯源的 ``config`` JSONB 字段应包含以下 CSS 选择器配置::

        {
            "article_selector": "article.post",
            "title_selector": "h2 a",
            "link_selector": "h2 a",
            "excerpt_selector": "p.summary"
        }

    ``link_selector`` 对应元素的 ``href`` 属性将作为资讯链接。
    """

    def __init__(self, timeout: float = _DEFAULT_TIMEOUT) -> None:
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect(self, source: Source) -> list[RawArticle]:
        """从网页采集资讯列表。"""
        config = source.config or {}
        article_selector = config.get("article_selector")
        title_selector = config.get("title_selector")
        link_selector = config.get("link_selector")

        if not article_selector or not title_selector or not link_selector:
            logger.warning(
                "Web source %s missing required CSS selectors in config", source.name
            )
            return []

        try:
            html = await self._fetch_page(source.url)
        except Exception:
            logger.exception("Failed to fetch web page: %s", source.url)
            return []

        soup = BeautifulSoup(html, "html.parser")
        containers = soup.select(article_selector)

        excerpt_selector = config.get("excerpt_selector")

        articles: list[RawArticle] = []
        for container in containers:
            try:
                article = self._parse_container(
                    container,
                    title_selector=title_selector,
                    link_selector=link_selector,
                    excerpt_selector=excerpt_selector,
                    base_url=source.url,
                    source_name=source.name,
                )
                if article is not None:
                    articles.append(article)
            except Exception:
                logger.warning(
                    "Skipping malformed article container on %s",
                    source.url,
                    exc_info=True,
                )
        return articles

    async def validate_source(self, source: Source) -> bool:
        """检查 URL 是否可达且返回 HTML 内容。"""
        try:
            html = await self._fetch_page(source.url)
            return bool(html and html.strip())
        except Exception:
            logger.debug(
                "Web source validation failed for %s", source.url, exc_info=True
            )
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_page(self, url: str) -> str:
        """使用 httpx 异步获取网页 HTML。"""
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; FashionIntelBot/1.0; "
                        "+https://github.com/fashion-intel)"
                    ),
                },
            )
            resp.raise_for_status()
            return resp.text

    @staticmethod
    def _parse_container(
        container: BeautifulSoup,
        *,
        title_selector: str,
        link_selector: str,
        excerpt_selector: str | None,
        base_url: str,
        source_name: str,
    ) -> RawArticle | None:
        """从单个文章容器中提取资讯数据。"""
        title_el = container.select_one(title_selector)
        if title_el is None:
            return None
        title = title_el.get_text(strip=True)
        if not title:
            return None

        link_el = container.select_one(link_selector)
        if link_el is None:
            return None
        href = link_el.get("href", "")
        if not href:
            return None
        # 处理相对链接
        url = urljoin(base_url, str(href))

        excerpt: str | None = None
        if excerpt_selector:
            excerpt_el = container.select_one(excerpt_selector)
            if excerpt_el is not None:
                excerpt = excerpt_el.get_text(strip=True) or None

        return RawArticle(
            original_title=title,
            original_url=url,
            original_language="en",
            original_excerpt=excerpt,
            published_at=None,
            source_name=source_name,
        )
