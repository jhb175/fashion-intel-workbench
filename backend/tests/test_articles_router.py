"""Tests for task 9.3 – article API routes registration and auth requirements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestArticleRoutesRegistered:
    """Verify that all article routes are registered on the FastAPI app."""

    def _get_routes(self):
        from app.main import app
        return [r.path for r in app.routes]

    def test_articles_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles" in routes

    def test_articles_detail_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}" in routes

    def test_articles_tags_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}/tags" in routes

    def test_articles_reprocess_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}/reprocess" in routes

    def test_articles_analyze_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}/analyze" in routes

    def test_articles_analysis_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}/analysis" in routes

    def test_articles_related_knowledge_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}/related-knowledge" in routes

    def test_articles_history_analysis_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/articles/{article_id}/history-analysis" in routes


class TestArticleRoutesRequireAuth:
    """Verify that all article endpoints require authentication (return 401 without token)."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_list_articles_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/articles")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_get_article_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/articles/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 401

    def test_update_tags_requires_auth(self):
        client = self._get_client()
        resp = client.patch(
            "/api/v1/articles/00000000-0000-0000-0000-000000000001/tags",
            json={"add": [], "remove": []},
        )
        assert resp.status_code == 401

    def test_reprocess_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/articles/00000000-0000-0000-0000-000000000001/reprocess")
        assert resp.status_code == 401

    def test_analyze_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/articles/00000000-0000-0000-0000-000000000001/analyze")
        assert resp.status_code == 401

    def test_get_analysis_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/articles/00000000-0000-0000-0000-000000000001/analysis")
        assert resp.status_code == 401

    def test_related_knowledge_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/articles/00000000-0000-0000-0000-000000000001/related-knowledge")
        assert resp.status_code == 401

    def test_history_analysis_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/articles/00000000-0000-0000-0000-000000000001/history-analysis")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/articles",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
