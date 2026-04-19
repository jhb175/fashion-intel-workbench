"""Tests for task 11.1 – briefing route registration and auth requirements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestBriefingRoutesRegistered:
    """Verify that all briefing routes are registered."""

    def _get_routes(self):
        from app.main import app
        return [r.path for r in app.routes]

    def test_briefings_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/briefings" in routes

    def test_briefings_detail_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/briefings/{briefing_id}" in routes

    def test_briefings_generate_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/briefings/generate" in routes


class TestBriefingRoutesRequireAuth:
    """Verify that all briefing endpoints require authentication."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    def test_list_briefings_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/briefings")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_get_briefing_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/briefings/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_generate_briefing_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/briefings/generate")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == 401

    def test_briefings_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/briefings",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_generate_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.post(
            "/api/v1/briefings/generate",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
