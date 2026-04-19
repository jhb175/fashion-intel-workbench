"""Pydantic models for authentication endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login request body."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT token pair returned after login or refresh."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public user representation returned by GET /api/v1/auth/me."""

    id: uuid.UUID
    username: str
    display_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
