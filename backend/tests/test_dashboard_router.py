"""Tests for task 14.1 – dashboard route registration and auth requirements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestDashboardRoutesRegistered:
    """Verify that all dashboard routes are registered."""

    def _get_routes(self):
        from app.main import app
        return [r.path for r in app.routes]

    def test_overview_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/dashboard/overview" in routes

    def test_recent_articles_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/dashboard/recent-articles" in routes

    def test_trending_tags_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/dashboard/trending-tags" in routes


class TestDashboardRoutesRequireAuth:
    """Verify that all dashboard endpoints require authentication."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    # --- No auth header ---

    def test_overview_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/dashboard/overview")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_recent_articles_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/dashboard/recent-articles")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_trending_tags_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/dashboard/trending-tags")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    # --- Invalid token ---

    def test_overview_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/dashboard/overview",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_recent_articles_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/dashboard/recent-articles",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_trending_tags_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/dashboard/trending-tags",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
