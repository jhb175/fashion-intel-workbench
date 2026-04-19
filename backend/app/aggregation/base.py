"""采集器抽象基类与原始资讯数据类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.source import Source


@dataclass
class RawArticle:
    """采集器返回的原始资讯数据。"""

    original_title: str
    original_url: str
    original_language: str = "en"
    original_excerpt: str | None = None
    published_at: datetime | None = None
    source_name: str = ""


class BaseCollector(ABC):
    """采集器基类。

    所有具体采集器（RSS、网页等）都应继承此类并实现
    ``collect`` 和 ``validate_source`` 方法。
    """

    @abstractmethod
    async def collect(self, source: Source) -> list[RawArticle]:
        """从指定资讯源采集原始资讯。

        Parameters
        ----------
        source:
            数据库中的资讯源记录。

        Returns
        -------
        list[RawArticle]
            采集到的原始资讯列表。如果采集失败应返回空列表而非抛出异常。
        """

    @abstractmethod
    async def validate_source(self, source: Source) -> bool:
        """验证资讯源是否可达。

        Parameters
        ----------
        source:
            数据库中的资讯源记录。

        Returns
        -------
        bool
            ``True`` 表示资讯源可达且格式正确。
        """
