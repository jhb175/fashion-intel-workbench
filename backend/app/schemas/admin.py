"""Pydantic models for admin management endpoints (sources, brands, keywords, monitor groups)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Source schemas
# ------------------------------------------------------------------


class SourceCreateRequest(BaseModel):
    """Request body for POST /api/v1/admin/sources."""

    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(
        ...,
        pattern=r"^(rss|web)$",
        description="Source type: rss or web",
    )
    monitor_group_id: uuid.UUID | None = None
    is_enabled: bool = True
    collect_interval_minutes: int = Field(60, ge=1)
    config: dict | None = None


class SourceUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/admin/sources/{id}."""

    name: str | None = Field(None, min_length=1, max_length=200)
    url: str | None = Field(None, min_length=1, max_length=500)
    source_type: str | None = Field(
        None,
        pattern=r"^(rss|web)$",
    )
    monitor_group_id: uuid.UUID | None = None
    is_enabled: bool | None = None
    collect_interval_minutes: int | None = Field(None, ge=1)
    config: dict | None = None


class SourceResponse(BaseModel):
    """Source representation in API responses."""

    id: uuid.UUID
    name: str
    url: str
    source_type: str
    monitor_group_id: uuid.UUID | None = None
    is_enabled: bool
    collect_interval_minutes: int
    last_collected_at: datetime | None = None
    last_collect_status: str | None = None
    last_error_message: str | None = None
    config: dict | None = None
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------
# Brand schemas
# ------------------------------------------------------------------


class BrandCreateRequest(BaseModel):
    """Request body for POST /api/v1/admin/brands."""

    name_zh: str = Field(..., min_length=1, max_length=200)
    name_en: str = Field(..., min_length=1, max_length=200)
    official_name: str | None = Field(None, max_length=200)
    social_media_name: str | None = Field(None, max_length=200)
    naming_notes: str | None = None
    monitor_group_id: uuid.UUID | None = None


class BrandUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/admin/brands/{id}."""

    name_zh: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = Field(None, min_length=1, max_length=200)
    official_name: str | None = Field(None, max_length=200)
    social_media_name: str | None = Field(None, max_length=200)
    naming_notes: str | None = None
    monitor_group_id: uuid.UUID | None = None


class BrandResponse(BaseModel):
    """Brand representation in API responses."""

    id: uuid.UUID
    name_zh: str
    name_en: str
    official_name: str | None = None
    social_media_name: str | None = None
    naming_notes: str | None = None
    monitor_group_id: uuid.UUID | None = None
    logo_count: int = 0
    created_at: datetime
    updated_at: datetime


class BrandNamingSearchResult(BaseModel):
    """Brand naming search result."""

    id: uuid.UUID
    name_zh: str
    name_en: str
    official_name: str | None = None
    social_media_name: str | None = None
    naming_notes: str | None = None


# ------------------------------------------------------------------
# Brand Logo schemas
# ------------------------------------------------------------------


class BrandLogoResponse(BaseModel):
    """Brand logo representation in API responses."""

    id: uuid.UUID
    brand_id: uuid.UUID
    file_name: str
    file_path: str
    file_format: str
    logo_type: str
    file_size_bytes: int | None = None
    thumbnail_path: str | None = None
    created_at: datetime


class BrandLogoUploadResponse(BaseModel):
    """Response after uploading a brand logo."""

    id: uuid.UUID
    brand_id: uuid.UUID
    file_name: str
    file_format: str
    logo_type: str
    file_size_bytes: int | None = None
    created_at: datetime


class BrandLogoUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/admin/brands/{id}/logos/{logo_id}."""

    logo_type: str | None = Field(
        None,
        pattern=r"^(main|horizontal|icon|monochrome|other)$",
    )
    file_name: str | None = Field(None, min_length=1, max_length=300)


# ------------------------------------------------------------------
# Keyword schemas
# ------------------------------------------------------------------


class KeywordCreateRequest(BaseModel):
    """Request body for POST /api/v1/admin/keywords."""

    word_zh: str = Field(..., min_length=1, max_length=200)
    word_en: str = Field(..., min_length=1, max_length=200)
    monitor_group_id: uuid.UUID | None = None


class KeywordUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/admin/keywords/{id}."""

    word_zh: str | None = Field(None, min_length=1, max_length=200)
    word_en: str | None = Field(None, min_length=1, max_length=200)
    monitor_group_id: uuid.UUID | None = None


class KeywordResponse(BaseModel):
    """Keyword representation in API responses."""

    id: uuid.UUID
    word_zh: str
    word_en: str
    monitor_group_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------
# Monitor Group schemas
# ------------------------------------------------------------------


class MonitorGroupUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/admin/monitor-groups/{id}."""

    display_name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    sort_order: int | None = None


class MonitorGroupResponse(BaseModel):
    """Monitor group representation in API responses."""

    id: uuid.UUID
    name: str
    display_name: str
    description: str | None = None
    sort_order: int
    source_count: int = 0
    brand_count: int = 0
    keyword_count: int = 0
    created_at: datetime
    updated_at: datetime
