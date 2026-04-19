"""Tests for task 10.1 – bookmark & topic candidate route registration and auth requirements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestBookmarkRoutesRegistered:
    """Verify that all bookmark and topic candidate routes are registered."""

    def _get_routes(self):
        from app.main import app
        return [r.path for r in app.routes]

    def test_bookmarks_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/bookmarks" in routes

    def test_bookmarks_add_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/bookmarks" in routes

    def test_bookmarks_remove_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/bookmarks/{article_id}" in routes

    def test_topic_candidates_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/topic-candidates" in routes

    def test_topic_candidates_add_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/topic-candidates" in routes

    def test_topic_candidates_remove_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/topic-candidates/{article_id}" in routes


class TestBookmarkRoutesRequireAuth:
    """Verify that all bookmark/topic-candidate endpoints require authentication."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    # --- Bookmarks ---

    def test_list_bookmarks_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/bookmarks")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_add_bookmark_requires_auth(self):
        client = self._get_client()
        resp = client.post(
            "/api/v1/bookmarks",
            json={"article_id": "00000000-0000-0000-0000-000000000001"},
        )
        assert resp.status_code == 401

    def test_remove_bookmark_requires_auth(self):
        client = self._get_client()
        resp = client.delete("/api/v1/bookmarks/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 401

    # --- Topic candidates ---

    def test_list_topic_candidates_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/topic-candidates")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_add_topic_candidate_requires_auth(self):
        client = self._get_client()
        resp = client.post(
            "/api/v1/topic-candidates",
            json={"article_id": "00000000-0000-0000-0000-000000000001"},
        )
        assert resp.status_code == 401

    def test_remove_topic_candidate_requires_auth(self):
        client = self._get_client()
        resp = client.delete("/api/v1/topic-candidates/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 401

    # --- Invalid token ---

    def test_bookmarks_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/bookmarks",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_topic_candidates_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/topic-candidates",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
