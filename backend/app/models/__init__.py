"""SQLAlchemy models — unified export for Alembic discovery."""

from app.models.ai_provider import AIProvider
from app.models.article import Article
from app.models.bookmark import Bookmark, TopicCandidate
from app.models.brand import Brand
from app.models.brand_logo import BrandLogo
from app.models.briefing import BriefingArticle, DailyBriefing
from app.models.deep_analysis import DeepAnalysis
from app.models.keyword import Keyword
from app.models.knowledge import (
    KnowledgeEntry,
    KnowledgeEntryBrand,
    KnowledgeEntryKeyword,
)
from app.models.monitor_group import MonitorGroup
from app.models.source import Source
from app.models.tag import ArticleTag
from app.models.user import User

__all__ = [
    "AIProvider",
    "Article",
    "ArticleTag",
    "Bookmark",
    "Brand",
    "BrandLogo",
    "BriefingArticle",
    "DailyBriefing",
    "DeepAnalysis",
    "Keyword",
    "KnowledgeEntry",
    "KnowledgeEntryBrand",
    "KnowledgeEntryKeyword",
    "MonitorGroup",
    "Source",
    "TopicCandidate",
    "User",
]
