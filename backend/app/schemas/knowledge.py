"""Pydantic models for knowledge base endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Enums
# ------------------------------------------------------------------


class KnowledgeCategory(str, Enum):
    """Allowed knowledge entry categories."""

    brand_profile = "brand_profile"
    style_history = "style_history"
    classic_item = "classic_item"
    person_profile = "person_profile"


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class KnowledgeEntryCreateRequest(BaseModel):
    """Request body for POST /api/v1/knowledge."""

    title: str = Field(..., min_length=1, max_length=300)
    category: KnowledgeCategory
    content: dict = Field(..., description="Structured JSONB content")
    summary: str | None = None
    brands: list[str] = Field(default_factory=list, description="Associated brand names")
    keywords: list[str] = Field(default_factory=list, description="Associated keywords")


class KnowledgeEntryUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/knowledge/{id}. All fields optional."""

    title: str | None = Field(None, min_length=1, max_length=300)
    category: KnowledgeCategory | None = None
    content: dict | None = None
    summary: str | None = None
    brands: list[str] | None = None
    keywords: list[str] | None = None


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class KnowledgeEntryResponse(BaseModel):
    """Single knowledge entry representation."""

    id: uuid.UUID
    title: str
    category: str
    content: dict
    summary: str | None = None
    brands: list[str]
    keywords: list[str]
    created_at: datetime
    updated_at: datetime


class KnowledgeEntryListResponse(BaseModel):
    """Paginated knowledge entry list."""

    items: list[KnowledgeEntryResponse]
    total: int
    page: int
    page_size: int
