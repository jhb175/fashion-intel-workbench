"""Pydantic models for AI provider configuration endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AIProviderCreateRequest(BaseModel):
    """POST /api/v1/ai-providers request body."""

    name: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1)
    api_base_url: str = Field(..., min_length=1, max_length=500)
    model_name: str = Field(..., min_length=1, max_length=200)


class AIProviderUpdateRequest(BaseModel):
    """PUT /api/v1/ai-providers/{id} request body.

    All fields are optional so callers can do partial updates.
    """

    name: str | None = Field(None, min_length=1, max_length=100)
    api_key: str | None = Field(None, min_length=1)
    api_base_url: str | None = Field(None, min_length=1, max_length=500)
    model_name: str | None = Field(None, min_length=1, max_length=200)


class AIProviderResponse(BaseModel):
    """Public representation of an AI provider (API Key masked)."""

    id: uuid.UUID
    name: str
    api_key_masked: str
    api_base_url: str
    model_name: str
    is_preset: bool
    is_active: bool
    last_test_at: datetime | None = None
    last_test_status: str | None = None
    created_at: datetime
    updated_at: datetime


class ConnectionTestResponse(BaseModel):
    """Result of an AI provider connection test."""

    status: str
    response_time_ms: int
    model_info: str | None = None
    error_type: str | None = None
    error_message: str | None = None
