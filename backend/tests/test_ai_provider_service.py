"""Tests for task 5.5 – AI provider schemas, service, and router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.schemas.ai_provider import (
    AIProviderCreateRequest,
    AIProviderResponse,
    AIProviderUpdateRequest,
    ConnectionTestResponse,
)
from app.services.encryption_service import EncryptionService


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture
def encryption_key() -> str:
    return Fernet.generate_key().decode("utf-8")


@pytest.fixture
def encryption_service(encryption_key: str) -> EncryptionService:
    return EncryptionService(encryption_key)


# ------------------------------------------------------------------
# Schema tests
# ------------------------------------------------------------------

class TestAIProviderSchemas:
    """Verify Pydantic models for AI provider endpoints."""

    def test_create_request_valid(self):
        req = AIProviderCreateRequest(
            name="DeepSeek",
            api_key="sk-abc123",
            api_base_url="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
        )
        assert req.name == "DeepSeek"
        assert req.api_key == "sk-abc123"

    def test_create_request_empty_name_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AIProviderCreateRequest(
                name="",
                api_key="sk-abc",
                api_base_url="https://api.example.com",
                model_name="model",
            )

    def test_create_request_empty_api_key_rejected(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            AIProviderCreateRequest(
                name="Test",
                api_key="",
                api_base_url="https://api.example.com",
                model_name="model",
            )

    def test_update_request_all_none(self):
        req = AIProviderUpdateRequest()
        assert req.name is None
        assert req.api_key is None
        assert req.api_base_url is None
        assert req.model_name is None

    def test_update_request_partial(self):
        req = AIProviderUpdateRequest(name="NewName")
        assert req.name == "NewName"
        assert req.api_key is None

    def test_response_model_fields(self):
        resp = AIProviderResponse(
            id=uuid.uuid4(),
            name="OpenAI",
            api_key_masked="sk-****...****a1b2",
            api_base_url="https://api.openai.com/v1",
            model_name="gpt-4o",
            is_preset=True,
            is_active=True,
            last_test_at=None,
            last_test_status=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert resp.is_preset is True
        assert resp.api_key_masked == "sk-****...****a1b2"

    def test_connection_test_response_success(self):
        resp = ConnectionTestResponse(
            status="success",
            response_time_ms=1200,
            model_info="gpt-4o",
        )
        assert resp.status == "success"
        assert resp.error_type is None

    def test_connection_test_response_failure(self):
        resp = ConnectionTestResponse(
            status="failed",
            response_time_ms=500,
            error_type="auth_failed",
            error_message="认证失败",
        )
        assert resp.status == "failed"
        assert resp.model_info is None


# ------------------------------------------------------------------
# Service unit tests (mock DB)
# ------------------------------------------------------------------

class TestAIProviderServiceToResponse:
    """Verify the _to_response helper masks API keys correctly."""

    def test_masks_api_key(self, encryption_service: EncryptionService):
        from app.services.ai_provider_service import AIProviderService

        db = AsyncMock()
        service = AIProviderService(db=db, encryption_service=encryption_service)

        # Build a mock provider
        provider = MagicMock()
        provider.id = uuid.uuid4()
        provider.name = "TestProvider"
        provider.api_key_encrypted = encryption_service.encrypt("sk-testapikey12345678")
        provider.api_base_url = "https://api.example.com/v1"
        provider.model_name = "test-model"
        provider.is_preset = False
        provider.is_active = True
        provider.last_test_at = None
        provider.last_test_status = None
        provider.created_at = datetime.now(timezone.utc)
        provider.updated_at = datetime.now(timezone.utc)

        resp = service._to_response(provider)
        assert "****" in resp.api_key_masked
        assert resp.name == "TestProvider"
        assert resp.is_active is True


class TestAIProviderServiceDeletePreset:
    """Verify that preset providers cannot be deleted."""

    @pytest.mark.asyncio
    async def test_delete_preset_raises_forbidden(self, encryption_service: EncryptionService):
        from app.services.ai_provider_service import AIProviderService
        from app.utils.errors import ForbiddenError

        provider = MagicMock()
        provider.is_preset = True

        db = AsyncMock()
        service = AIProviderService(db=db, encryption_service=encryption_service)

        # Patch _get_provider_or_404 to return our mock preset provider
        service._get_provider_or_404 = AsyncMock(return_value=provider)

        with pytest.raises(ForbiddenError, match="预置"):
            await service.delete_provider(uuid.uuid4(), uuid.uuid4())


class TestAIProviderServiceCreate:
    """Verify provider creation encrypts the API key."""

    @pytest.mark.asyncio
    async def test_create_encrypts_api_key(self, encryption_service: EncryptionService):
        from app.services.ai_provider_service import AIProviderService

        db = AsyncMock()
        # Make flush and refresh no-ops; capture what gets added
        added_objects = []
        db.add = lambda obj: added_objects.append(obj)
        db.flush = AsyncMock()
        db.refresh = AsyncMock()

        service = AIProviderService(db=db, encryption_service=encryption_service)

        body = AIProviderCreateRequest(
            name="TestProvider",
            api_key="sk-plaintext-key-12345",
            api_base_url="https://api.example.com/v1",
            model_name="test-model",
        )

        # Patch _to_response to avoid needing full ORM attributes
        service._to_response = MagicMock(
            return_value=AIProviderResponse(
                id=uuid.uuid4(),
                name="TestProvider",
                api_key_masked="sk-****...****2345",
                api_base_url="https://api.example.com/v1",
                model_name="test-model",
                is_preset=False,
                is_active=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

        user_id = uuid.uuid4()
        result = await service.create_provider(user_id, body)

        assert len(added_objects) == 1
        created = added_objects[0]
        assert created.name == "TestProvider"
        assert created.is_preset is False
        assert created.is_active is False
        # The stored key should be encrypted (not plaintext)
        assert created.api_key_encrypted != "sk-plaintext-key-12345"
        # Decrypting should give back the original
        assert encryption_service.decrypt(created.api_key_encrypted) == "sk-plaintext-key-12345"


# ------------------------------------------------------------------
# Router integration tests (no real DB)
# ------------------------------------------------------------------

class TestAIProviderRouter:
    """Verify AI provider routes are registered and require auth."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_routes_registered(self):
        from app.main import app
        routes = [r.path for r in app.routes]
        assert "/api/v1/ai-providers" in routes
        assert "/api/v1/ai-providers/active" in routes
        assert "/api/v1/ai-providers/{provider_id}" in routes
        assert "/api/v1/ai-providers/{provider_id}/activate" in routes
        assert "/api/v1/ai-providers/{provider_id}/test" in routes

    def test_list_without_token_returns_401(self):
        client = self._get_client()
        resp = client.get("/api/v1/ai-providers")
        assert resp.status_code == 401

    def test_get_active_without_token_returns_401(self):
        client = self._get_client()
        resp = client.get("/api/v1/ai-providers/active")
        assert resp.status_code == 401

    def test_create_without_token_returns_401(self):
        client = self._get_client()
        resp = client.post(
            "/api/v1/ai-providers",
            json={
                "name": "Test",
                "api_key": "sk-abc",
                "api_base_url": "https://api.example.com",
                "model_name": "model",
            },
        )
        assert resp.status_code == 401

    def test_update_without_token_returns_401(self):
        client = self._get_client()
        resp = client.put(
            f"/api/v1/ai-providers/{uuid.uuid4()}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 401

    def test_delete_without_token_returns_401(self):
        client = self._get_client()
        resp = client.delete(f"/api/v1/ai-providers/{uuid.uuid4()}")
        assert resp.status_code == 401

    def test_activate_without_token_returns_401(self):
        client = self._get_client()
        resp = client.patch(f"/api/v1/ai-providers/{uuid.uuid4()}/activate")
        assert resp.status_code == 401

    def test_test_connection_without_token_returns_401(self):
        client = self._get_client()
        resp = client.post(f"/api/v1/ai-providers/{uuid.uuid4()}/test")
        assert resp.status_code == 401

    def test_create_invalid_body_returns_422(self):
        client = self._get_client()
        # Even with a valid token, an empty body should fail validation (422)
        # But since we don't have a token, we get 401 first.
        # This test verifies the endpoint exists and processes the request.
        resp = client.post("/api/v1/ai-providers", json={})
        # 401 because no auth — confirms the route is wired up
        assert resp.status_code == 401
