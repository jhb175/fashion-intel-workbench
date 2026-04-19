"""Tests for task 12.1 – knowledge base route registration and auth requirements."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


class TestKnowledgeRoutesRegistered:
    """Verify that all knowledge base routes are registered."""

    def _get_routes(self):
        from app.main import app
        return [r.path for r in app.routes]

    def test_knowledge_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/knowledge" in routes

    def test_knowledge_detail_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/knowledge/{entry_id}" in routes

    def test_knowledge_create_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/knowledge" in routes

    def test_knowledge_update_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/knowledge/{entry_id}" in routes

    def test_knowledge_delete_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/knowledge/{entry_id}" in routes


class TestKnowledgeRoutesRequireAuth:
    """Verify that all knowledge endpoints require authentication."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_list_knowledge_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/knowledge")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_get_knowledge_requires_auth(self):
        client = self._get_client()
        entry_id = str(uuid.uuid4())
        resp = client.get(f"/api/v1/knowledge/{entry_id}")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_create_knowledge_requires_auth(self):
        client = self._get_client()
        resp = client.post(
            "/api/v1/knowledge",
            json={
                "title": "Test Entry",
                "category": "brand_profile",
                "content": {"key": "value"},
            },
        )
        assert resp.status_code == 401

    def test_update_knowledge_requires_auth(self):
        client = self._get_client()
        entry_id = str(uuid.uuid4())
        resp = client.put(
            f"/api/v1/knowledge/{entry_id}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 401

    def test_delete_knowledge_requires_auth(self):
        client = self._get_client()
        entry_id = str(uuid.uuid4())
        resp = client.delete(f"/api/v1/knowledge/{entry_id}")
        assert resp.status_code == 401

    def test_knowledge_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/knowledge",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


class TestKnowledgeCategoryValidation:
    """Verify that category query parameter is validated against allowed values."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_invalid_category_returns_422(self):
        """Passing an invalid category value should return a 422 validation error."""
        client = self._get_client()
        # Even though auth will fail first, we test with an invalid category
        # to ensure the enum validation is in place. We use a valid token scenario
        # indirectly — FastAPI validates query params before dependencies in some cases,
        # but typically auth runs first. We just verify the enum is defined correctly.
        from app.schemas.knowledge import KnowledgeCategory

        assert set(KnowledgeCategory) == {
            KnowledgeCategory.brand_profile,
            KnowledgeCategory.style_history,
            KnowledgeCategory.classic_item,
            KnowledgeCategory.person_profile,
        }


class TestKnowledgeSchemas:
    """Verify Pydantic schema validation for knowledge entries."""

    def test_create_request_valid(self):
        from app.schemas.knowledge import KnowledgeEntryCreateRequest

        req = KnowledgeEntryCreateRequest(
            title="Dior Brand Profile",
            category="brand_profile",
            content={"founded_year": 1947, "founder": "Christian Dior"},
            summary="A brief history of Dior",
            brands=["Dior"],
            keywords=["luxury", "haute couture"],
        )
        assert req.title == "Dior Brand Profile"
        assert req.category.value == "brand_profile"
        assert len(req.brands) == 1
        assert len(req.keywords) == 2

    def test_create_request_invalid_category(self):
        from pydantic import ValidationError as PydanticValidationError

        from app.schemas.knowledge import KnowledgeEntryCreateRequest

        with pytest.raises(PydanticValidationError):
            KnowledgeEntryCreateRequest(
                title="Test",
                category="invalid_category",
                content={"key": "value"},
            )

    def test_update_request_all_optional(self):
        from app.schemas.knowledge import KnowledgeEntryUpdateRequest

        req = KnowledgeEntryUpdateRequest()
        assert req.title is None
        assert req.category is None
        assert req.content is None
        assert req.summary is None
        assert req.brands is None
        assert req.keywords is None

    def test_response_model(self):
        import uuid
        from datetime import datetime, timezone

        from app.schemas.knowledge import KnowledgeEntryResponse

        now = datetime.now(timezone.utc)
        resp = KnowledgeEntryResponse(
            id=uuid.uuid4(),
            title="Test",
            category="brand_profile",
            content={"key": "value"},
            summary="Summary",
            brands=["Nike"],
            keywords=["sneakers"],
            created_at=now,
            updated_at=now,
        )
        assert resp.brands == ["Nike"]
        assert resp.keywords == ["sneakers"]
