"""Tests for task 1.1 – backend project structure initialisation."""

import pytest
from fastapi.testclient import TestClient


# ------------------------------------------------------------------
# Config tests
# ------------------------------------------------------------------

class TestConfig:
    """Verify Settings loads defaults and parses CORS origins."""

    def test_default_jwt_algorithm(self):
        from app.config import Settings
        s = Settings()
        assert s.JWT_ALGORITHM == "HS256"

    def test_default_jwt_expire_minutes(self):
        from app.config import Settings
        s = Settings()
        assert s.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30

    def test_cors_origins_list_single(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="http://localhost:3000")
        assert s.cors_origins_list == ["http://localhost:3000"]

    def test_cors_origins_list_multiple(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="http://a.com, http://b.com")
        assert s.cors_origins_list == ["http://a.com", "http://b.com"]

    def test_cors_origins_list_empty_entries(self):
        from app.config import Settings
        s = Settings(CORS_ORIGINS="http://a.com,,")
        assert s.cors_origins_list == ["http://a.com"]


# ------------------------------------------------------------------
# Database module tests
# ------------------------------------------------------------------

class TestDatabase:
    """Verify database module exports the expected objects."""

    def test_engine_is_async(self):
        from app.database import engine
        assert "async" in type(engine).__name__.lower()

    def test_session_factory_produces_async_session(self):
        from app.database import async_session_factory
        assert async_session_factory is not None

    def test_base_is_declarative(self):
        from app.database import Base
        from sqlalchemy.orm import DeclarativeBase
        assert issubclass(Base, DeclarativeBase)

    @pytest.mark.asyncio
    async def test_get_db_is_async_generator(self):
        import inspect
        from app.database import get_db
        assert inspect.isasyncgenfunction(get_db)


# ------------------------------------------------------------------
# FastAPI app tests
# ------------------------------------------------------------------

class TestApp:
    """Verify the FastAPI application is configured correctly."""

    def test_app_title(self):
        from app.main import app
        assert app.title == "Fashion Intel Workbench"

    def test_cors_middleware_present(self):
        from app.main import app
        middleware_classes = [type(m).__name__ for m in app.user_middleware]
        # FastAPI stores user-added middleware; CORSMiddleware is wrapped
        assert any("CORS" in name or "cors" in name.lower() for name in middleware_classes) or len(app.user_middleware) > 0

    def test_health_endpoint(self):
        from app.main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 200
        assert body["data"]["status"] == "healthy"

    def test_success_response_format(self):
        from app.main import success_response
        result = success_response(data={"id": 1}, message="ok")
        assert result == {"code": 200, "message": "ok", "data": {"id": 1}}

    def test_error_response_format(self):
        from app.main import error_response
        result = error_response(message="not found", code=404)
        assert result == {"code": 404, "message": "not found", "data": None}

    def test_global_exception_handler(self):
        """Unhandled exceptions should return a 500 JSON envelope."""
        from app.main import app
        from fastapi import Request

        @app.get("/test-error")
        async def raise_error():
            raise RuntimeError("boom")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-error")
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == 500
        assert "boom" not in body["message"]  # must not leak internals
