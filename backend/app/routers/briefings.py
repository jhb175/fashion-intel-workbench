"""Daily briefing API router."""

from __future__ import annotations

import uuid
from datetime import date, timezone, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.responses import success_response
from app.schemas.briefing import BriefingGenerateRequest
from app.services.ai_provider_adapter import AIProviderAdapter
from app.services.ai_service import AIService
from app.services.briefing_service import BriefingService
from app.services.encryption_service import EncryptionService
from app.utils.auth import get_current_user

router = APIRouter(tags=["briefings"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------


def _get_briefing_service(db: AsyncSession = Depends(get_db)) -> BriefingService:
    """BriefingService without AI (for read-only endpoints)."""
    return BriefingService(db=db)


def _get_briefing_service_with_ai(db: AsyncSession = Depends(get_db)) -> BriefingService:
    """BriefingService with AI service wired up (for generation)."""
    encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
    adapter = AIProviderAdapter(encryption_service, db)
    ai_service = AIService(adapter)
    return BriefingService(db=db, ai_service=ai_service)


# ===========================================================================
# Briefing endpoints
# ===========================================================================


@router.get("/api/v1/briefings")
async def list_briefings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: BriefingService = Depends(_get_briefing_service),
) -> dict:
    """Get briefing list ordered by date descending with pagination."""
    result = await service.list_briefings(page=page, page_size=page_size)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/api/v1/briefings/{briefing_id}")
async def get_briefing(
    briefing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BriefingService = Depends(_get_briefing_service),
) -> dict:
    """Get a single briefing by ID."""
    result = await service.get_briefing(briefing_id)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/api/v1/briefings/generate")
async def generate_briefing(
    body: BriefingGenerateRequest | None = None,
    current_user: User = Depends(get_current_user),
    service: BriefingService = Depends(_get_briefing_service_with_ai),
) -> dict:
    """Manually trigger daily briefing generation.

    If no date is provided, defaults to today (UTC).
    """
    briefing_date = (body.briefing_date if body and body.briefing_date else None) or datetime.now(timezone.utc).date()
    result = await service.generate_briefing(briefing_date)
    return success_response(data=result.model_dump(mode="json"))
