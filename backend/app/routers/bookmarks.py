"""Bookmark and topic candidate API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.responses import success_response
from app.schemas.bookmark import BookmarkCreateRequest, BookmarkFiltersQuery
from app.services.bookmark_service import BookmarkService
from app.utils.auth import get_current_user

router = APIRouter(tags=["bookmarks"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_bookmark_service(db: AsyncSession = Depends(get_db)) -> BookmarkService:
    return BookmarkService(db=db)


# ===========================================================================
# Bookmark endpoints
# ===========================================================================


@router.get("/api/v1/bookmarks")
async def list_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    brand: str | None = Query(None),
    content_type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(_get_bookmark_service),
) -> dict:
    """Get bookmark list with optional filtering and pagination."""
    from datetime import date as date_type

    filters = BookmarkFiltersQuery(
        page=page,
        page_size=page_size,
        brand=brand,
        content_type=content_type,
        start_date=date_type.fromisoformat(start_date) if start_date else None,
        end_date=date_type.fromisoformat(end_date) if end_date else None,
    )
    result = await service.list_bookmarks(current_user.id, filters)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/api/v1/bookmarks")
async def add_bookmark(
    body: BookmarkCreateRequest,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(_get_bookmark_service),
) -> dict:
    """Add a bookmark for the current user."""
    bookmark = await service.add_bookmark(current_user.id, body.article_id)
    return success_response(data=bookmark.model_dump(mode="json"))


@router.delete("/api/v1/bookmarks/{article_id}")
async def remove_bookmark(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(_get_bookmark_service),
) -> dict:
    """Remove a bookmark by article_id for the current user."""
    await service.remove_bookmark(current_user.id, article_id)
    return success_response(message="收藏已取消")


# ===========================================================================
# Topic candidate endpoints
# ===========================================================================


@router.get("/api/v1/topic-candidates")
async def list_topic_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    brand: str | None = Query(None),
    content_type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(_get_bookmark_service),
) -> dict:
    """Get topic candidate list with optional filtering and pagination."""
    from datetime import date as date_type

    filters = BookmarkFiltersQuery(
        page=page,
        page_size=page_size,
        brand=brand,
        content_type=content_type,
        start_date=date_type.fromisoformat(start_date) if start_date else None,
        end_date=date_type.fromisoformat(end_date) if end_date else None,
    )
    result = await service.list_topic_candidates(current_user.id, filters)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/api/v1/topic-candidates")
async def add_topic_candidate(
    body: BookmarkCreateRequest,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(_get_bookmark_service),
) -> dict:
    """Add a topic candidate for the current user."""
    candidate = await service.add_topic_candidate(current_user.id, body.article_id)
    return success_response(data=candidate.model_dump(mode="json"))


@router.delete("/api/v1/topic-candidates/{article_id}")
async def remove_topic_candidate(
    article_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BookmarkService = Depends(_get_bookmark_service),
) -> dict:
    """Remove a topic candidate by article_id for the current user."""
    await service.remove_topic_candidate(current_user.id, article_id)
    return success_response(message="待选题已取消")
