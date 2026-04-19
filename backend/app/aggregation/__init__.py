"""资讯聚合引擎 — 采集器与去重服务。"""

from app.aggregation.base import BaseCollector, RawArticle
from app.aggregation.dedup import DeduplicationService
from app.aggregation.rss_collector import RSSCollector
from app.aggregation.web_collector import WebCollector

__all__ = [
    "BaseCollector",
    "DeduplicationService",
    "RSSCollector",
    "RawArticle",
    "WebCollector",
]
