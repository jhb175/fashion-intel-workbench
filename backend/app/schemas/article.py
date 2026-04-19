"""Pydantic models for article-related endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Tag schemas
# ------------------------------------------------------------------


class ArticleTagResponse(BaseModel):
    """Representation of a single article tag."""

    id: uuid.UUID
    tag_type: str
    tag_value: str
    is_auto: bool
    created_at: datetime


class TagUpdateRequest(BaseModel):
    """Request body for PATCH /api/v1/articles/{id}/tags.

    Callers supply the tags to add and/or remove.
    """

    add: list[TagItem] | None = Field(
        None, description="Tags to add to the article"
    )
    remove: list[uuid.UUID] | None = Field(
        None, description="Tag IDs to remove from the article"
    )


class TagItem(BaseModel):
    """A single tag to be added."""

    tag_type: str = Field(
        ...,
        pattern=r"^(brand|monitor_group|content_type|keyword)$",
        description="Tag type: brand, monitor_group, content_type, or keyword",
    )
    tag_value: str = Field(..., min_length=1, max_length=200)


# Fix forward reference – TagUpdateRequest references TagItem which is
# defined after it.  We redefine TagUpdateRequest below so the forward
# ref resolves cleanly.

class TagUpdateRequest(BaseModel):  # noqa: F811
    """Request body for PATCH /api/v1/articles/{id}/tags."""

    add: list[TagItem] | None = Field(
        None, description="Tags to add to the article"
    )
    remove: list[uuid.UUID] | None = Field(
        None, description="Tag IDs to remove from the article"
    )


# ------------------------------------------------------------------
# Article response schemas
# ------------------------------------------------------------------


class ArticleResponse(BaseModel):
    """Full article representation with tags and user-specific status."""

    id: uuid.UUID
    source_id: uuid.UUID
    original_title: str
    original_url: str
    original_language: str
    original_excerpt: str | None = None
    chinese_summary: str | None = None
    published_at: datetime | None = None
    collected_at: datetime
    processing_status: str
    tags: list[ArticleTagResponse] = []
    is_bookmarked: bool = False
    is_topic_candidate: bool = False
    created_at: datetime
    updated_at: datetime


class ArticleListItem(BaseModel):
    """Lightweight article representation for list views."""

    id: uuid.UUID
    original_title: str
    original_url: str
    original_language: str
    chinese_summary: str | None = None
    published_at: datetime | None = None
    collected_at: datetime
    processing_status: str
    tags: list[ArticleTagResponse] = []
    is_bookmarked: bool = False
    is_topic_candidate: bool = False


class ArticleListResponse(BaseModel):
    """Paginated article list."""

    items: list[ArticleListItem]
    total: int
    page: int
    page_size: int


# ------------------------------------------------------------------
# Query / filter schemas
# ------------------------------------------------------------------


class ArticleFiltersQuery(BaseModel):
    """Query parameters for GET /api/v1/articles."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    brand: str | None = None
    monitor_group: str | None = None
    content_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    keyword: str | None = None
    status: str | None = None
