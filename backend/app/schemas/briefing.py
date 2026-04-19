"""Pydantic models for briefing endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------


class BriefingGenerateRequest(BaseModel):
    """Request body for POST /api/v1/briefings/generate.

    If *briefing_date* is omitted the server defaults to today (UTC).
    """

    briefing_date: date | None = None


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class BriefingResponse(BaseModel):
    """Single briefing representation (detail view)."""

    id: uuid.UUID
    briefing_date: date
    content: dict[str, Any]
    has_new_articles: bool
    created_at: datetime


class BriefingListItem(BaseModel):
    """Lightweight briefing item for list views."""

    id: uuid.UUID
    briefing_date: date
    has_new_articles: bool
    summary: str = ""
    created_at: datetime


class BriefingListResponse(BaseModel):
    """Paginated briefing list."""

    items: list[BriefingListItem]
    total: int
    page: int
    page_size: int
