"""去重服务 — 基于 original_url 唯一性 + 标题相似度。"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.aggregation.base import RawArticle
from app.models.article import Article

logger = logging.getLogger(__name__)

# 标题相似度阈值：超过此值视为重复
SIMILARITY_THRESHOLD = 0.85


class DeduplicationService:
    """去重服务。

    判断逻辑：
    1. 精确匹配 ``original_url`` — 如果数据库中已存在相同 URL 则为重复。
    2. 标题相似度 — 对标题进行归一化后计算字符级相似度
       （``SequenceMatcher``），超过阈值 0.85 则视为重复。
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def is_duplicate(self, article: RawArticle) -> bool:
        """判断资讯是否与数据库中已有记录重复。"""
        # 1. URL 精确匹配
        if await self._url_exists(article.original_url):
            return True

        # 2. 标题相似度匹配（通过 title_hash 快速定位候选集）
        title_hash = self.compute_title_hash(article.original_title)
        # 先尝试精确 hash 匹配
        if await self._title_hash_exists(title_hash):
            return True

        # 再对最近的文章做模糊标题比较（限制范围避免全表扫描）
        candidates = await self._get_recent_titles(limit=200)
        for existing_title in candidates:
            similarity = self.compute_title_similarity(
                article.original_title, existing_title
            )
            if similarity >= SIMILARITY_THRESHOLD:
                return True

        return False

    # ------------------------------------------------------------------
    # 标题相似度计算
    # ------------------------------------------------------------------

    @staticmethod
    def compute_title_similarity(title_a: str, title_b: str) -> float:
        """计算两个标题的相似度（0.0 ~ 1.0）。

        步骤：
        1. 归一化标题（小写、去除标点和多余空白）。
        2. 使用 ``SequenceMatcher`` 计算字符级相似度比率。
        """
        norm_a = _normalize_title(title_a)
        norm_b = _normalize_title(title_b)
        if not norm_a and not norm_b:
            return 1.0
        if not norm_a or not norm_b:
            return 0.0
        return SequenceMatcher(None, norm_a, norm_b).ratio()

    @staticmethod
    def compute_title_hash(title: str) -> str:
        """计算标题的 SHA-256 哈希（基于归一化后的标题）。"""
        normalized = _normalize_title(title)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 数据库查询
    # ------------------------------------------------------------------

    async def _url_exists(self, url: str) -> bool:
        stmt = select(Article.id).where(Article.original_url == url).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _title_hash_exists(self, title_hash: str) -> bool:
        stmt = select(Article.id).where(Article.title_hash == title_hash).limit(1)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _get_recent_titles(self, limit: int = 200) -> list[str]:
        """获取最近的文章标题用于模糊比较。"""
        stmt = (
            select(Article.original_title)
            .order_by(Article.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return [row[0] for row in result.all()]


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------

# 匹配标点和特殊符号的正则
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_title(title: str) -> str:
    """归一化标题：小写 → 去除标点 → 合并空白 → 去首尾空白。"""
    text = title.lower()
    text = unicodedata.normalize("NFKC", text)
    text = _PUNCT_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text
