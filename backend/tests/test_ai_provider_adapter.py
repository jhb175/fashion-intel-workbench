"""Unit tests for the AIProviderAdapter and error classification logic."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest
from cryptography.fernet import Fernet

from app.models.ai_provider import AIProvider
from app.services.ai_provider_adapter import (
    ERROR_AUTH_FAILED,
    ERROR_MODEL_NOT_FOUND,
    ERROR_NETWORK_TIMEOUT,
    ERROR_QUOTA_EXCEEDED,
    ERROR_SERVER_ERROR,
    AIProviderAdapter,
    ConnectionTestResult,
    classify_ai_error,
)
from app.services.encryption_service import EncryptionService
from app.utils.errors import AIServiceError, NotFoundError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def encryption_service() -> EncryptionService:
    key = Fernet.generate_key().decode("utf-8")
    return EncryptionService(key)


@pytest.fixture
def mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def adapter(encryption_service: EncryptionService, mock_db: AsyncMock) -> AIProviderAdapter:
    return AIProviderAdapter(encryption_service=encryption_service, db=mock_db)


def _make_provider(encryption_service: EncryptionService, **overrides) -> AIProvider:
    """Create a fake AIProvider with encrypted API key."""
    provider = MagicMock(spec=AIProvider)
    provider.id = overrides.get("id", uuid.uuid4())
    provider.name = overrides.get("name", "TestProvider")
    provider.api_key_encrypted = encryption_service.encrypt(
        overrides.get("api_key", "sk-test-key-12345")
    )
    provider.api_base_url = overrides.get("api_base_url", "https://api.openai.com/v1")
    provider.model_name = overrides.get("model_name", "gpt-4o")
    provider.is_active = overrides.get("is_active", True)
    provider.is_preset = overrides.get("is_preset", False)
    return provider


# ---------------------------------------------------------------------------
# classify_ai_error tests
# ---------------------------------------------------------------------------


class TestClassifyAIError:
    """Tests for the classify_ai_error helper function."""

    def test_authentication_error(self) -> None:
        exc = openai.AuthenticationError(
            message="Invalid API key",
            response=httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com")),
            body=None,
        )
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_AUTH_FAILED
        assert "认证失败" in msg

    def test_rate_limit_error(self) -> None:
        exc = openai.RateLimitError(
            message="Rate limit exceeded",
            response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com")),
            body=None,
        )
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_QUOTA_EXCEEDED
        assert "配额" in msg

    def test_not_found_error(self) -> None:
        exc = openai.NotFoundError(
            message="Model not found",
            response=httpx.Response(404, request=httpx.Request("POST", "https://api.openai.com")),
            body=None,
        )
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_MODEL_NOT_FOUND
        assert "模型" in msg

    def test_timeout_error_openai(self) -> None:
        exc = openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com"))
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_NETWORK_TIMEOUT
        assert "超时" in msg

    def test_timeout_error_httpx(self) -> None:
        exc = httpx.TimeoutException("Connection timed out")
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_NETWORK_TIMEOUT
        assert "超时" in msg

    def test_server_error_500(self) -> None:
        exc = openai.InternalServerError(
            message="Internal server error",
            response=httpx.Response(500, request=httpx.Request("POST", "https://api.openai.com")),
            body=None,
        )
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_SERVER_ERROR
        assert "服务" in msg

    def test_server_error_503(self) -> None:
        exc = openai.APIStatusError(
            message="Service unavailable",
            response=httpx.Response(503, request=httpx.Request("POST", "https://api.openai.com")),
            body=None,
        )
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_SERVER_ERROR

    def test_connection_error(self) -> None:
        exc = openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com"))
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_NETWORK_TIMEOUT
        assert "网络" in msg

    def test_unknown_exception_fallback(self) -> None:
        exc = RuntimeError("Something unexpected")
        error_type, msg = classify_ai_error(exc)
        assert error_type == ERROR_SERVER_ERROR
        assert "AI 服务调用失败" in msg


# ---------------------------------------------------------------------------
# get_active_provider tests
# ---------------------------------------------------------------------------


class TestGetActiveProvider:
    """Tests for AIProviderAdapter.get_active_provider."""

    async def test_returns_active_provider(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService, mock_db: AsyncMock
    ) -> None:
        provider = _make_provider(encryption_service)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = provider
        mock_db.execute.return_value = mock_result

        result = await adapter.get_active_provider()
        assert result is provider

    async def test_raises_not_found_when_no_active(
        self, adapter: AIProviderAdapter, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(NotFoundError, match="未找到激活的 AI 提供者"):
            await adapter.get_active_provider()


# ---------------------------------------------------------------------------
# create_client tests
# ---------------------------------------------------------------------------


class TestCreateClient:
    """Tests for AIProviderAdapter.create_client."""

    async def test_creates_client_with_correct_config(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService, mock_db: AsyncMock
    ) -> None:
        provider = _make_provider(
            encryption_service,
            api_key="sk-real-key-abc",
            api_base_url="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = provider
        mock_db.execute.return_value = mock_result

        client, returned_provider = await adapter.create_client()

        assert isinstance(client, openai.AsyncOpenAI)
        assert str(client.base_url).rstrip("/") == "https://api.deepseek.com/v1"
        assert returned_provider is provider


# ---------------------------------------------------------------------------
# chat_completion tests
# ---------------------------------------------------------------------------


class TestChatCompletion:
    """Tests for AIProviderAdapter.chat_completion."""

    async def test_successful_completion(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService, mock_db: AsyncMock
    ) -> None:
        provider = _make_provider(encryption_service, model_name="gpt-4o")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = provider
        mock_db.execute.return_value = mock_result

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            MockClient.return_value = mock_client_instance

            result = await adapter.chat_completion(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result == "Hello, world!"
        mock_client_instance.chat.completions.create.assert_called_once()
        call_kwargs = mock_client_instance.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o"

    async def test_completion_raises_ai_service_error_on_auth_failure(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService, mock_db: AsyncMock
    ) -> None:
        provider = _make_provider(encryption_service)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = provider
        mock_db.execute.return_value = mock_result

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.side_effect = (
                openai.AuthenticationError(
                    message="Invalid API key",
                    response=httpx.Response(
                        401, request=httpx.Request("POST", "https://api.openai.com")
                    ),
                    body=None,
                )
            )
            MockClient.return_value = mock_client_instance

            with pytest.raises(AIServiceError, match="认证失败"):
                await adapter.chat_completion(
                    messages=[{"role": "user", "content": "Hi"}]
                )

    async def test_completion_handles_none_content(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService, mock_db: AsyncMock
    ) -> None:
        provider = _make_provider(encryption_service)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = provider
        mock_db.execute.return_value = mock_result

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            MockClient.return_value = mock_client_instance

            result = await adapter.chat_completion(
                messages=[{"role": "user", "content": "Hi"}]
            )

        assert result == ""


# ---------------------------------------------------------------------------
# test_connection tests
# ---------------------------------------------------------------------------


class TestTestConnection:
    """Tests for AIProviderAdapter.test_connection."""

    async def test_successful_connection(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService
    ) -> None:
        provider = _make_provider(encryption_service)

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hi"

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.return_value = mock_response
            MockClient.return_value = mock_client_instance

            result = await adapter.test_connection(provider)

        assert isinstance(result, ConnectionTestResult)
        assert result.status == "success"
        assert result.response_time_ms >= 0
        assert result.error_type is None
        assert result.error_message is None

    async def test_failed_connection_auth(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService
    ) -> None:
        provider = _make_provider(encryption_service)

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.side_effect = (
                openai.AuthenticationError(
                    message="Invalid API key",
                    response=httpx.Response(
                        401, request=httpx.Request("POST", "https://api.openai.com")
                    ),
                    body=None,
                )
            )
            MockClient.return_value = mock_client_instance

            result = await adapter.test_connection(provider)

        assert result.status == "failed"
        assert result.error_type == ERROR_AUTH_FAILED
        assert result.error_message is not None
        assert result.response_time_ms >= 0

    async def test_failed_connection_timeout(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService
    ) -> None:
        provider = _make_provider(encryption_service)

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.side_effect = (
                openai.APITimeoutError(
                    request=httpx.Request("POST", "https://api.openai.com")
                )
            )
            MockClient.return_value = mock_client_instance

            result = await adapter.test_connection(provider)

        assert result.status == "failed"
        assert result.error_type == ERROR_NETWORK_TIMEOUT

    async def test_failed_connection_server_error(
        self, adapter: AIProviderAdapter, encryption_service: EncryptionService
    ) -> None:
        provider = _make_provider(encryption_service)

        with patch("app.services.ai_provider_adapter.AsyncOpenAI") as MockClient:
            mock_client_instance = AsyncMock()
            mock_client_instance.chat.completions.create.side_effect = (
                openai.InternalServerError(
                    message="Internal server error",
                    response=httpx.Response(
                        500, request=httpx.Request("POST", "https://api.openai.com")
                    ),
                    body=None,
                )
            )
            MockClient.return_value = mock_client_instance

            result = await adapter.test_connection(provider)

        assert result.status == "failed"
        assert result.error_type == ERROR_SERVER_ERROR


# ---------------------------------------------------------------------------
# ConnectionTestResult tests
# ---------------------------------------------------------------------------


class TestConnectionTestResult:
    """Tests for the ConnectionTestResult dataclass."""

    def test_success_result(self) -> None:
        result = ConnectionTestResult(status="success", response_time_ms=150)
        assert result.status == "success"
        assert result.response_time_ms == 150
        assert result.error_type is None
        assert result.error_message is None

    def test_failed_result(self) -> None:
        result = ConnectionTestResult(
            status="failed",
            response_time_ms=5000,
            error_type=ERROR_NETWORK_TIMEOUT,
            error_message="Connection timed out",
        )
        assert result.status == "failed"
        assert result.error_type == ERROR_NETWORK_TIMEOUT
        assert result.error_message == "Connection timed out"
