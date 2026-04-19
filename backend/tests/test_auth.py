"""Tests for task 4.1 – authentication service, schemas, router, and error handling."""

from __future__ import annotations

import uuid
from datetime import timedelta

import jwt
import pytest
from fastapi.testclient import TestClient


# ------------------------------------------------------------------
# Error classes tests
# ------------------------------------------------------------------

class TestErrorClasses:
    """Verify business exception classes and their attributes."""

    def test_validation_error_status_code(self):
        from app.utils.errors import ValidationError
        exc = ValidationError()
        assert exc.status_code == 400

    def test_authentication_error_status_code(self):
        from app.utils.errors import AuthenticationError
        exc = AuthenticationError()
        assert exc.status_code == 401

    def test_forbidden_error_status_code(self):
        from app.utils.errors import ForbiddenError
        exc = ForbiddenError()
        assert exc.status_code == 403

    def test_not_found_error_status_code(self):
        from app.utils.errors import NotFoundError
        exc = NotFoundError()
        assert exc.status_code == 404

    def test_conflict_error_status_code(self):
        from app.utils.errors import ConflictError
        exc = ConflictError()
        assert exc.status_code == 409

    def test_ai_service_error_status_code(self):
        from app.utils.errors import AIServiceError
        exc = AIServiceError()
        assert exc.status_code == 502

    def test_external_service_error_status_code(self):
        from app.utils.errors import ExternalServiceError
        exc = ExternalServiceError()
        assert exc.status_code == 503

    def test_custom_message(self):
        from app.utils.errors import NotFoundError
        exc = NotFoundError("User not found")
        assert exc.message == "User not found"

    def test_default_message(self):
        from app.utils.errors import NotFoundError
        exc = NotFoundError()
        assert exc.message == "Resource not found"

    def test_app_error_is_base(self):
        from app.utils.errors import AppError, AuthenticationError
        assert issubclass(AuthenticationError, AppError)


# ------------------------------------------------------------------
# Exception handler integration tests
# ------------------------------------------------------------------

class TestExceptionHandlers:
    """Verify that business exceptions return the unified JSON envelope."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_authentication_error_response_format(self):
        from app.main import app
        from app.utils.errors import AuthenticationError

        @app.get("/test-auth-error")
        async def raise_auth_error():
            raise AuthenticationError("bad token")

        client = self._get_client()
        resp = client.get("/test-auth-error")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401
        assert body["message"] == "bad token"
        assert body["data"] is None

    def test_not_found_error_response_format(self):
        from app.main import app
        from app.utils.errors import NotFoundError

        @app.get("/test-not-found-error")
        async def raise_not_found():
            raise NotFoundError()

        client = self._get_client()
        resp = client.get("/test-not-found-error")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == 404
        assert body["message"] == "Resource not found"
        assert body["data"] is None

    def test_validation_error_response_format(self):
        from app.main import app
        from app.utils.errors import ValidationError

        @app.get("/test-validation-error")
        async def raise_validation():
            raise ValidationError("bad input")

        client = self._get_client()
        resp = client.get("/test-validation-error")
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == 400
        assert body["message"] == "bad input"


# ------------------------------------------------------------------
# Password hashing tests
# ------------------------------------------------------------------

class TestPasswordHashing:
    """Verify bcrypt password hashing and verification."""

    def test_hash_password_returns_string(self):
        from app.utils.auth import hash_password
        h = hash_password("secret123")
        assert isinstance(h, str)
        assert h != "secret123"

    def test_verify_password_correct(self):
        from app.utils.auth import hash_password, verify_password
        h = hash_password("mypassword")
        assert verify_password("mypassword", h) is True

    def test_verify_password_incorrect(self):
        from app.utils.auth import hash_password, verify_password
        h = hash_password("mypassword")
        assert verify_password("wrongpassword", h) is False

    def test_hash_is_unique_per_call(self):
        from app.utils.auth import hash_password
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt


# ------------------------------------------------------------------
# JWT token tests
# ------------------------------------------------------------------

class TestJWTTokens:
    """Verify JWT token generation and decoding."""

    def test_create_access_token_returns_string(self):
        from app.utils.auth import create_access_token
        token = create_access_token(uuid.uuid4())
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        from app.utils.auth import create_access_token, decode_access_token
        uid = uuid.uuid4()
        token = create_access_token(uid)
        payload = decode_access_token(token)
        assert payload["sub"] == str(uid)
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_expired_token_raises(self):
        from app.utils.auth import create_access_token, decode_access_token
        from app.utils.errors import AuthenticationError
        token = create_access_token(uuid.uuid4(), expires_delta=timedelta(seconds=-1))
        with pytest.raises(AuthenticationError, match="expired"):
            decode_access_token(token)

    def test_decode_invalid_token_raises(self):
        from app.utils.auth import decode_access_token
        from app.utils.errors import AuthenticationError
        with pytest.raises(AuthenticationError, match="Invalid token"):
            decode_access_token("not.a.valid.token")

    def test_decode_tampered_token_raises(self):
        from app.utils.auth import create_access_token, decode_access_token
        from app.utils.errors import AuthenticationError
        token = create_access_token(uuid.uuid4())
        # Tamper with the token
        tampered = token[:-4] + "XXXX"
        with pytest.raises(AuthenticationError):
            decode_access_token(tampered)


# ------------------------------------------------------------------
# Auth schemas tests
# ------------------------------------------------------------------

class TestAuthSchemas:
    """Verify Pydantic models for auth endpoints."""

    def test_login_request_valid(self):
        from app.schemas.auth import LoginRequest
        req = LoginRequest(username="admin", password="secret")
        assert req.username == "admin"
        assert req.password == "secret"

    def test_login_request_empty_username_rejected(self):
        from app.schemas.auth import LoginRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LoginRequest(username="", password="secret")

    def test_login_request_empty_password_rejected(self):
        from app.schemas.auth import LoginRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LoginRequest(username="admin", password="")

    def test_token_response_defaults(self):
        from app.schemas.auth import TokenResponse
        resp = TokenResponse(access_token="abc123")
        assert resp.token_type == "bearer"

    def test_user_response_from_attributes(self):
        from app.schemas.auth import UserResponse
        assert UserResponse.model_config.get("from_attributes") is True


# ------------------------------------------------------------------
# Auth router integration tests (no real DB)
# ------------------------------------------------------------------

class TestAuthRouter:
    """Verify auth endpoints return correct status codes and formats."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_login_missing_body_returns_422(self):
        client = self._get_client()
        resp = client.post("/api/v1/auth/login")
        assert resp.status_code == 422

    def test_me_without_token_returns_401(self):
        client = self._get_client()
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_me_with_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_refresh_without_token_returns_401(self):
        client = self._get_client()
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    def test_auth_routes_registered(self):
        from app.main import app
        routes = [r.path for r in app.routes]
        assert "/api/v1/auth/login" in routes
        assert "/api/v1/auth/refresh" in routes
        assert "/api/v1/auth/me" in routes
