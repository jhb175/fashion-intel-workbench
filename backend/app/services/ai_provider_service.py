"""AI provider configuration management service – CRUD, activation, testing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider import AIProvider
from app.schemas.ai_provider import (
    AIProviderCreateRequest,
    AIProviderResponse,
    AIProviderUpdateRequest,
    ConnectionTestResponse,
)
from app.services.ai_provider_adapter import AIProviderAdapter
from app.services.encryption_service import EncryptionService
from app.utils.errors import ForbiddenError, NotFoundError


class AIProviderService:
    """Business logic for AI provider configuration management."""

    def __init__(
        self,
        db: AsyncSession,
        encryption_service: EncryptionService,
    ) -> None:
        self.db = db
        self.encryption_service = encryption_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _to_response(self, provider: AIProvider) -> AIProviderResponse:
        """Convert an ORM model to a response DTO with the API key masked."""
        decrypted_key = self.encryption_service.decrypt(provider.api_key_encrypted)
        masked_key = EncryptionService.mask_api_key(decrypted_key)
        return AIProviderResponse(
            id=provider.id,
            name=provider.name,
            api_key_masked=masked_key,
            api_base_url=provider.api_base_url,
            model_name=provider.model_name,
            is_preset=provider.is_preset,
            is_active=provider.is_active,
            last_test_at=provider.last_test_at,
            last_test_status=provider.last_test_status,
            created_at=provider.created_at,
            updated_at=provider.updated_at,
        )

    async def _get_provider_or_404(
        self, provider_id: uuid.UUID, user_id: uuid.UUID
    ) -> AIProvider:
        """Fetch a provider belonging to *user_id* or raise ``NotFoundError``."""
        stmt = select(AIProvider).where(
            AIProvider.id == provider_id,
            AIProvider.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider is None:
            raise NotFoundError("AI 提供者配置不存在")
        return provider

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    async def list_providers(self, user_id: uuid.UUID) -> list[AIProviderResponse]:
        """Return all AI provider configs for a user (API keys masked)."""
        stmt = (
            select(AIProvider)
            .where(AIProvider.user_id == user_id)
            .order_by(AIProvider.created_at)
        )
        result = await self.db.execute(stmt)
        providers = result.scalars().all()
        return [self._to_response(p) for p in providers]

    # ------------------------------------------------------------------
    # Get active
    # ------------------------------------------------------------------

    async def get_active_provider(self, user_id: uuid.UUID) -> AIProviderResponse:
        """Return the currently active AI provider for a user."""
        stmt = select(AIProvider).where(
            AIProvider.user_id == user_id,
            AIProvider.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider is None:
            raise NotFoundError("未找到激活的 AI 提供者配置")
        return self._to_response(provider)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    async def create_provider(
        self, user_id: uuid.UUID, body: AIProviderCreateRequest
    ) -> AIProviderResponse:
        """Create a new custom AI provider configuration."""
        encrypted_key = self.encryption_service.encrypt(body.api_key)
        provider = AIProvider(
            user_id=user_id,
            name=body.name,
            api_key_encrypted=encrypted_key,
            api_base_url=body.api_base_url,
            model_name=body.model_name,
            is_preset=False,
            is_active=False,
        )
        self.db.add(provider)
        await self.db.flush()
        await self.db.refresh(provider)
        return self._to_response(provider)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_provider(
        self,
        provider_id: uuid.UUID,
        user_id: uuid.UUID,
        body: AIProviderUpdateRequest,
    ) -> AIProviderResponse:
        """Update an existing AI provider configuration."""
        provider = await self._get_provider_or_404(provider_id, user_id)

        if body.name is not None:
            provider.name = body.name
        if body.api_key is not None:
            provider.api_key_encrypted = self.encryption_service.encrypt(body.api_key)
        if body.api_base_url is not None:
            provider.api_base_url = body.api_base_url
        if body.model_name is not None:
            provider.model_name = body.model_name

        await self.db.flush()
        await self.db.refresh(provider)
        return self._to_response(provider)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete_provider(
        self, provider_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Delete a custom AI provider. Preset providers cannot be deleted."""
        provider = await self._get_provider_or_404(provider_id, user_id)
        if provider.is_preset:
            raise ForbiddenError("预置 AI 提供者不可删除")
        await self.db.delete(provider)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Activate
    # ------------------------------------------------------------------

    async def activate_provider(
        self, provider_id: uuid.UUID, user_id: uuid.UUID
    ) -> AIProviderResponse:
        """Set a provider as the active one (deactivate all others first)."""
        provider = await self._get_provider_or_404(provider_id, user_id)

        # Deactivate all providers for this user
        await self.db.execute(
            update(AIProvider)
            .where(AIProvider.user_id == user_id)
            .values(is_active=False)
        )

        # Activate the selected provider
        provider.is_active = True
        await self.db.flush()
        await self.db.refresh(provider)
        return self._to_response(provider)

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    async def test_connection(
        self, provider_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConnectionTestResponse:
        """Test the connection to an AI provider and persist the result."""
        provider = await self._get_provider_or_404(provider_id, user_id)

        adapter = AIProviderAdapter(
            encryption_service=self.encryption_service,
            db=self.db,
        )
        result = adapter.test_connection(provider)
        # test_connection is async
        test_result = await result

        # Persist test result on the provider row
        provider.last_test_at = datetime.now(timezone.utc)
        provider.last_test_status = test_result.status
        provider.last_test_error = test_result.error_message
        await self.db.flush()

        return ConnectionTestResponse(
            status=test_result.status,
            response_time_ms=test_result.response_time_ms,
            model_info=provider.model_name if test_result.status == "success" else None,
            error_type=test_result.error_type,
            error_message=test_result.error_message,
        )
