"""Article API router — list, detail, tag editing, reprocess, deep analysis,
related knowledge, and history analysis endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.deep_analysis import DeepAnalysis
from app.models.knowledge import KnowledgeEntry
from app.models.user import User
from app.responses import success_response
from app.schemas.article import (
    ArticleFiltersQuery,
    TagUpdateRequest,
)
from app.services.ai_provider_adapter import AIProviderAdapter
from app.services.ai_service import AIService, ArticleTags
from app.services.article_service import ArticleService
from app.services.encryption_service import EncryptionService
from app.services.search_service import SearchService
from app.tasks.ai_tasks import reprocess_article as reprocess_article_task
from app.utils.auth import get_current_user
from app.utils.errors import NotFoundError

router = APIRouter(prefix="/api/v1/articles", tags=["articles"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_article_service(db: AsyncSession = Depends(get_db)) -> ArticleService:
    return ArticleService(db=db)


def _get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(db=db)


def _build_ai_service(db: AsyncSession) -> AIService:
    """Build an AIService with EncryptionService and AIProviderAdapter."""
    encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
    adapter = AIProviderAdapter(encryption_service, db)
    return AIService(adapter)


# ---------------------------------------------------------------------------
# GET /api/v1/articles — article list (filtered, searched, paginated)
# ---------------------------------------------------------------------------


@router.get("")
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    brand: str | None = Query(None),
    monitor_group: str | None = Query(None),
    content_type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    keyword: str | None = Query(None),
    status: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(_get_search_service),
) -> dict:
    """Get article list with filtering, search, and pagination."""
    from datetime import date as date_type

    filters = ArticleFiltersQuery(
        page=page,
        page_size=page_size,
        brand=brand,
        monitor_group=monitor_group,
        content_type=content_type,
        start_date=date_type.fromisoformat(start_date) if start_date else None,
        end_date=date_type.fromisoformat(end_date) if end_date else None,
        keyword=keyword,
        status=status,
    )
    result = await search_service.search_articles(filters, user_id=current_user.id)
    return success_response(data=result.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# GET /api/v1/articles/{article_id} — article detail
# ---------------------------------------------------------------------------


@router.get("/{article_id}")
async def get_article(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ArticleService = Depends(_get_article_service),
) -> dict:
    """Get article detail with tags and bookmark/topic status."""
    article = await service.get_article(article_id, user_id=current_user.id)
    return success_response(data=article.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# PATCH /api/v1/articles/{article_id}/tags — edit article tags
# ---------------------------------------------------------------------------


@router.patch("/{article_id}/tags")
async def update_article_tags(
    article_id: uuid.UUID,
    body: TagUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ArticleService = Depends(_get_article_service),
) -> dict:
    """Add and/or remove tags on an article."""
    tags = await service.update_tags(article_id, body)
    return success_response(data=[t.model_dump(mode="json") for t in tags])


# ---------------------------------------------------------------------------
# POST /api/v1/articles/{article_id}/reprocess — trigger AI reprocessing
# ---------------------------------------------------------------------------


@router.post("/{article_id}/reprocess")
async def reprocess_article(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ArticleService = Depends(_get_article_service),
) -> dict:
    """Manually trigger AI reprocessing for an article."""
    article = await service.reprocess_article(article_id)
    # Dispatch Celery task for async AI reprocessing
    reprocess_article_task.delay(str(article_id))
    return success_response(data=article.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# POST /api/v1/articles/{article_id}/analyze — trigger AI deep analysis
# ---------------------------------------------------------------------------


@router.post("/{article_id}/analyze")
async def trigger_deep_analysis(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger AI deep analysis for an article and store the result."""
    # Load article via service to validate existence
    article_service = ArticleService(db=db)
    article_resp = await article_service.get_article(article_id)

    # Build AI service
    ai_service = _build_ai_service(db)

    # Build ArticleTags from the article's existing tags
    tags = ArticleTags(
        brands=[t.tag_value for t in article_resp.tags if t.tag_type == "brand"],
        monitor_groups=[t.tag_value for t in article_resp.tags if t.tag_type == "monitor_group"],
        content_types=[t.tag_value for t in article_resp.tags if t.tag_type == "content_type"],
        keywords=[t.tag_value for t in article_resp.tags if t.tag_type == "keyword"],
    )

    # Generate deep analysis via AI
    analysis_result = await ai_service.generate_deep_analysis(
        title=article_resp.original_title,
        summary=article_resp.chinese_summary or article_resp.original_title,
        tags=tags,
    )

    # Upsert into deep_analyses table
    stmt = select(DeepAnalysis).where(DeepAnalysis.article_id == article_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.importance = analysis_result.importance
        existing.industry_background = analysis_result.industry_background
        existing.follow_up_suggestions = analysis_result.follow_up_suggestions
    else:
        deep_analysis = DeepAnalysis(
            article_id=article_id,
            importance=analysis_result.importance,
            industry_background=analysis_result.industry_background,
            follow_up_suggestions=analysis_result.follow_up_suggestions,
        )
        db.add(deep_analysis)

    await db.flush()

    return success_response(data={
        "article_id": str(article_id),
        "importance": analysis_result.importance,
        "industry_background": analysis_result.industry_background,
        "follow_up_suggestions": analysis_result.follow_up_suggestions,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/articles/{article_id}/analysis — get deep analysis result
# ---------------------------------------------------------------------------


@router.get("/{article_id}/analysis")
async def get_deep_analysis(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get the stored AI deep analysis result for an article."""
    stmt = select(DeepAnalysis).where(DeepAnalysis.article_id == article_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise NotFoundError("该资讯尚未进行深度分析")

    return success_response(data={
        "id": str(analysis.id),
        "article_id": str(analysis.article_id),
        "importance": analysis.importance,
        "industry_background": analysis.industry_background,
        "follow_up_suggestions": analysis.follow_up_suggestions,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    })


# ---------------------------------------------------------------------------
# GET /api/v1/articles/{article_id}/related-knowledge
# ---------------------------------------------------------------------------


@router.get("/{article_id}/related-knowledge")
async def get_related_knowledge(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get knowledge entries related to an article based on tag matching."""
    # Load article to get tags
    article_service = ArticleService(db=db)
    article_resp = await article_service.get_article(article_id)

    # Build ArticleTags
    article_tags = ArticleTags(
        brands=[t.tag_value for t in article_resp.tags if t.tag_type == "brand"],
        monitor_groups=[t.tag_value for t in article_resp.tags if t.tag_type == "monitor_group"],
        content_types=[t.tag_value for t in article_resp.tags if t.tag_type == "content_type"],
        keywords=[t.tag_value for t in article_resp.tags if t.tag_type == "keyword"],
    )

    # Load all knowledge entries
    ke_stmt = select(KnowledgeEntry)
    ke_result = await db.execute(ke_stmt)
    all_entries = list(ke_result.scalars().all())

    # Match using AI service (non-AI, tag-based matching)
    ai_service = _build_ai_service(db)
    matched = await ai_service.match_knowledge_entries(article_tags, all_entries)

    # Serialize matched entries
    data = [
        {
            "id": str(entry.id),
            "title": entry.title,
            "category": entry.category,
            "summary": entry.summary,
            "brands": [b.brand_name for b in (entry.brands or [])],
            "keywords": [k.keyword for k in (entry.keywords or [])],
        }
        for entry in matched
    ]

    return success_response(data=data)


# ---------------------------------------------------------------------------
# POST /api/v1/articles/{article_id}/history-analysis
# ---------------------------------------------------------------------------


@router.post("/{article_id}/history-analysis")
async def trigger_history_analysis(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger AI history analysis for an article using related knowledge."""
    # Load article
    article_service = ArticleService(db=db)
    article_resp = await article_service.get_article(article_id)

    # Build ArticleTags
    article_tags = ArticleTags(
        brands=[t.tag_value for t in article_resp.tags if t.tag_type == "brand"],
        monitor_groups=[t.tag_value for t in article_resp.tags if t.tag_type == "monitor_group"],
        content_types=[t.tag_value for t in article_resp.tags if t.tag_type == "content_type"],
        keywords=[t.tag_value for t in article_resp.tags if t.tag_type == "keyword"],
    )

    # Load all knowledge entries and find related ones
    ke_stmt = select(KnowledgeEntry)
    ke_result = await db.execute(ke_stmt)
    all_entries = list(ke_result.scalars().all())

    ai_service = _build_ai_service(db)
    related_entries = await ai_service.match_knowledge_entries(article_tags, all_entries)

    # Generate history analysis
    article_summary = article_resp.chinese_summary or article_resp.original_title
    analysis_text = await ai_service.generate_history_analysis(
        article_summary=article_summary,
        knowledge_entries=related_entries,
    )

    return success_response(data={
        "article_id": str(article_id),
        "history_analysis": analysis_text,
        "related_knowledge_count": len(related_entries),
    })
