"""AI provider adapter layer — unified wrapper for OpenAI-compatible API calls."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import openai
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_provider import AIProvider
from app.services.encryption_service import EncryptionService
from app.utils.errors import AIServiceError, NotFoundError


# ---------------------------------------------------------------------------
# Error type constants
# ---------------------------------------------------------------------------

ERROR_AUTH_FAILED = "auth_failed"
ERROR_QUOTA_EXCEEDED = "quota_exceeded"
ERROR_NETWORK_TIMEOUT = "network_timeout"
ERROR_MODEL_NOT_FOUND = "model_not_found"
ERROR_SERVER_ERROR = "server_error"


# ---------------------------------------------------------------------------
# Connection test result
# ---------------------------------------------------------------------------


@dataclass
class ConnectionTestResult:
    """Result of an AI provider connection test."""

    status: str  # "success" | "failed"
    response_time_ms: int
    error_type: str | None = None
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Error classification helper
# ---------------------------------------------------------------------------


def classify_ai_error(exc: Exception) -> tuple[str, str]:
    """Classify an AI-related exception into an error type and message.

    Returns:
        A ``(error_type, error_message)`` tuple.
    """
    if isinstance(exc, openai.AuthenticationError):
        return ERROR_AUTH_FAILED, "认证失败：API Key 无效或已过期"

    if isinstance(exc, openai.RateLimitError):
        return ERROR_QUOTA_EXCEEDED, "配额不足：请检查 API 账户余额或稍后重试"

    if isinstance(exc, openai.NotFoundError):
        return ERROR_MODEL_NOT_FOUND, "模型不存在：请检查模型名称是否正确"

    if isinstance(exc, (openai.APITimeoutError, httpx.TimeoutException)):
        return ERROR_NETWORK_TIMEOUT, "网络超时：请检查网络连接或 API URL 是否正确"

    if isinstance(exc, openai.APIStatusError) and exc.status_code >= 500:
        return ERROR_SERVER_ERROR, "服务暂时不可用，请稍后重试"

    # Fallback: treat any other openai API error as server error
    if isinstance(exc, openai.APIStatusError):
        return ERROR_SERVER_ERROR, f"AI 服务调用失败：HTTP {exc.status_code}"

    if isinstance(exc, openai.APIConnectionError):
        return ERROR_NETWORK_TIMEOUT, "网络连接失败：请检查网络连接或 API URL 是否正确"

    return ERROR_SERVER_ERROR, f"AI 服务调用失败：{exc}"


# ---------------------------------------------------------------------------
# AI Provider Adapter
# ---------------------------------------------------------------------------


class AIProviderAdapter:
    """AI provider adapter — unified wrapper for OpenAI-compatible API calls.

    Uses the ``openai`` Python SDK's ``base_url`` parameter to support
    multiple providers (OpenAI, DeepSeek, Anthropic, etc.) through a single
    client interface.
    """

    def __init__(self, encryption_service: EncryptionService, db: AsyncSession) -> None:
        self.encryption_service = encryption_service
        self.db = db

    # ------------------------------------------------------------------
    # Provider lookup
    # ------------------------------------------------------------------

    async def get_active_provider(self) -> AIProvider:
        """Return the currently active AI provider from the database.

        Raises:
            NotFoundError: If no active provider is configured.
        """
        stmt = select(AIProvider).where(AIProvider.is_active.is_(True))
        result = await self.db.execute(stmt)
        provider = result.scalar_one_or_none()
        if provider is None:
            raise NotFoundError("未找到激活的 AI 提供者配置，请先在设置页配置并激活一个 AI 提供者")
        return provider

    # ------------------------------------------------------------------
    # Client creation
    # ------------------------------------------------------------------

    async def create_client(self) -> tuple[AsyncOpenAI, AIProvider]:
        """Create an ``AsyncOpenAI`` client using the active provider config.

        Returns:
            A tuple of ``(client, provider)`` so callers can access the
            provider's ``model_name`` without an extra DB query.
        """
        provider = await self.get_active_provider()
        api_key = self.encryption_service.decrypt(provider.api_key_encrypted)
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=provider.api_base_url,
        )
        return client, provider

    # ------------------------------------------------------------------
    # Chat completion
    # ------------------------------------------------------------------

    async def chat_completion(self, messages: list[dict], **kwargs) -> str:
        """Send a Chat Completions request and return the response text.

        The active provider's ``model_name`` is used automatically.  Any
        extra ``kwargs`` are forwarded to the underlying SDK call (e.g.
        ``temperature``, ``max_tokens``).

        Raises:
            AIServiceError: On any AI API failure, with a classified
                ``error_type`` attribute.
        """
        try:
            client, provider = await self.create_client()
            response = await client.chat.completions.create(
                model=provider.model_name,
                messages=messages,
                **kwargs,
            )
            choice = response.choices[0]
            return choice.message.content or ""
        except Exception as exc:
            error_type, error_message = classify_ai_error(exc)
            raise AIServiceError(error_message) from exc

    # ------------------------------------------------------------------
    # Connection test
    # ------------------------------------------------------------------

    async def test_connection(self, provider: AIProvider) -> ConnectionTestResult:
        """Test the connection to a specific AI provider.

        Sends a minimal Chat Completions request (``"Hi"``) and measures
        the round-trip time.  Returns a :class:`ConnectionTestResult`
        regardless of success or failure — the caller decides how to
        surface the result.
        """
        api_key = self.encryption_service.decrypt(provider.api_key_encrypted)
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=provider.api_base_url,
        )

        start = time.monotonic()
        try:
            await client.chat.completions.create(
                model=provider.model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ConnectionTestResult(
                status="success",
                response_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            error_type, error_message = classify_ai_error(exc)
            return ConnectionTestResult(
                status="failed",
                response_time_ms=elapsed_ms,
                error_type=error_type,
                error_message=error_message,
            )
