"""Pydantic models for bookmark and topic candidate endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class BookmarkCreateRequest(BaseModel):
    """Request body for POST /api/v1/bookmarks and POST /api/v1/topic-candidates."""

    article_id: uuid.UUID


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class BookmarkArticleBrief(BaseModel):
    """Nested article summary inside a bookmark response."""

    id: uuid.UUID
    original_title: str
    original_url: str
    original_language: str
    chinese_summary: str | None = None
    published_at: datetime | None = None
    processing_status: str


class BookmarkResponse(BaseModel):
    """Single bookmark / topic-candidate representation."""

    id: uuid.UUID
    user_id: uuid.UUID
    article_id: uuid.UUID
    article: BookmarkArticleBrief | None = None
    created_at: datetime


class BookmarkListResponse(BaseModel):
    """Paginated bookmark / topic-candidate list."""

    items: list[BookmarkResponse]
    total: int
    page: int
    page_size: int


# ------------------------------------------------------------------
# Query / filter schemas
# ------------------------------------------------------------------


class BookmarkFiltersQuery(BaseModel):
    """Query parameters for GET /api/v1/bookmarks and /api/v1/topic-candidates."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    brand: str | None = None
    content_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
