"""Authentication API router – login, refresh, and current-user endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.responses import success_response
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.utils.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    verify_password,
)
from app.utils.errors import AuthenticationError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Authenticate a user and return a JWT access token."""
    result = await db.execute(
        select(User).where(User.username == body.username)
    )
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise AuthenticationError("Invalid username or password")

    if not user.is_active:
        raise AuthenticationError("User account is disabled")

    token = create_access_token(user.id)
    return success_response(
        data=TokenResponse(access_token=token).model_dump(),
    )


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Issue a fresh access token for an already-authenticated user.

    The caller must provide a valid (non-expired) token in the
    ``Authorization`` header.  A new token with a fresh expiry is returned.
    """
    token = create_access_token(current_user.id)
    return success_response(
        data=TokenResponse(access_token=token).model_dump(),
    )


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return the profile of the currently authenticated user."""
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(mode="json"),
    )
