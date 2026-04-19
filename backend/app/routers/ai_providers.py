"""AI provider configuration API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.responses import success_response
from app.schemas.ai_provider import (
    AIProviderCreateRequest,
    AIProviderUpdateRequest,
)
from app.services.ai_provider_service import AIProviderService
from app.services.encryption_service import EncryptionService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/ai-providers", tags=["ai-providers"])


def _get_service(db: AsyncSession = Depends(get_db)) -> AIProviderService:
    """Build an ``AIProviderService`` with the current DB session."""
    encryption_service = EncryptionService(settings.ENCRYPTION_KEY)
    return AIProviderService(db=db, encryption_service=encryption_service)


@router.get("")
async def list_providers(
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Get all AI provider configurations (API keys masked)."""
    providers = await service.list_providers(current_user.id)
    return success_response(data=[p.model_dump(mode="json") for p in providers])


@router.get("/active")
async def get_active_provider(
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Get the currently active AI provider."""
    provider = await service.get_active_provider(current_user.id)
    return success_response(data=provider.model_dump(mode="json"))


@router.post("")
async def create_provider(
    body: AIProviderCreateRequest,
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Add a custom AI provider configuration."""
    provider = await service.create_provider(current_user.id, body)
    return success_response(data=provider.model_dump(mode="json"))


@router.put("/{provider_id}")
async def update_provider(
    provider_id: uuid.UUID,
    body: AIProviderUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Edit an AI provider configuration."""
    provider = await service.update_provider(provider_id, current_user.id, body)
    return success_response(data=provider.model_dump(mode="json"))


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Delete a custom AI provider (preset providers cannot be deleted)."""
    await service.delete_provider(provider_id, current_user.id)
    return success_response(message="AI 提供者已删除")


@router.patch("/{provider_id}/activate")
async def activate_provider(
    provider_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Set an AI provider as the currently active one."""
    provider = await service.activate_provider(provider_id, current_user.id)
    return success_response(data=provider.model_dump(mode="json"))


@router.post("/{provider_id}/test")
async def test_provider_connection(
    provider_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: AIProviderService = Depends(_get_service),
) -> dict:
    """Test an AI provider's connection."""
    result = await service.test_connection(provider_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))
