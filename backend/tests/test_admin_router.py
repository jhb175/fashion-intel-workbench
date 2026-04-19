"""Tests for task 13.1 – admin API routes registration and auth requirements."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAdminRoutesRegistered:
    """Verify that all admin routes are registered on the FastAPI app."""

    def _get_routes(self):
        from app.main import app
        return [r.path for r in app.routes]

    # --- Sources ---

    def test_sources_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/sources" in routes

    def test_sources_create_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/sources" in routes

    def test_sources_update_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/sources/{source_id}" in routes

    def test_sources_toggle_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/sources/{source_id}/toggle" in routes

    def test_sources_delete_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/sources/{source_id}" in routes

    # --- Brands ---

    def test_brands_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands" in routes

    def test_brands_create_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands" in routes

    def test_brands_update_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}" in routes

    def test_brands_delete_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}" in routes

    def test_brands_search_naming_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/search-naming" in routes

    # --- Brand Logos ---

    def test_brand_logos_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}/logos" in routes

    def test_brand_logos_upload_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}/logos" in routes

    def test_brand_logos_update_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}/logos/{logo_id}" in routes

    def test_brand_logos_delete_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}/logos/{logo_id}" in routes

    def test_brand_logos_download_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/brands/{brand_id}/logos/{logo_id}/download" in routes

    # --- Keywords ---

    def test_keywords_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/keywords" in routes

    def test_keywords_create_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/keywords" in routes

    def test_keywords_update_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/keywords/{keyword_id}" in routes

    def test_keywords_delete_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/keywords/{keyword_id}" in routes

    # --- Monitor Groups ---

    def test_monitor_groups_list_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/monitor-groups" in routes

    def test_monitor_groups_update_route_registered(self):
        routes = self._get_routes()
        assert "/api/v1/admin/monitor-groups/{group_id}" in routes


class TestAdminRoutesRequireAuth:
    """Verify that all admin endpoints require authentication (return 401 without token)."""

    def _get_client(self):
        from app.main import app
        return TestClient(app, raise_server_exceptions=False)

    _FAKE_UUID = "00000000-0000-0000-0000-000000000001"

    # --- Sources ---

    def test_list_sources_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/admin/sources")
        assert resp.status_code == 401

    def test_create_source_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/admin/sources", json={
            "name": "Test", "url": "https://example.com", "source_type": "rss",
        })
        assert resp.status_code == 401

    def test_update_source_requires_auth(self):
        client = self._get_client()
        resp = client.put(f"/api/v1/admin/sources/{self._FAKE_UUID}", json={"name": "Updated"})
        assert resp.status_code == 401

    def test_toggle_source_requires_auth(self):
        client = self._get_client()
        resp = client.patch(f"/api/v1/admin/sources/{self._FAKE_UUID}/toggle")
        assert resp.status_code == 401

    def test_delete_source_requires_auth(self):
        client = self._get_client()
        resp = client.delete(f"/api/v1/admin/sources/{self._FAKE_UUID}")
        assert resp.status_code == 401

    # --- Brands ---

    def test_list_brands_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/admin/brands")
        assert resp.status_code == 401

    def test_create_brand_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/admin/brands", json={
            "name_zh": "测试", "name_en": "Test",
        })
        assert resp.status_code == 401

    def test_update_brand_requires_auth(self):
        client = self._get_client()
        resp = client.put(f"/api/v1/admin/brands/{self._FAKE_UUID}", json={"name_zh": "更新"})
        assert resp.status_code == 401

    def test_delete_brand_requires_auth(self):
        client = self._get_client()
        resp = client.delete(f"/api/v1/admin/brands/{self._FAKE_UUID}")
        assert resp.status_code == 401

    def test_search_naming_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/admin/brands/search-naming?q=nike")
        assert resp.status_code == 401

    # --- Brand Logos ---

    def test_list_logos_requires_auth(self):
        client = self._get_client()
        resp = client.get(f"/api/v1/admin/brands/{self._FAKE_UUID}/logos")
        assert resp.status_code == 401

    def test_upload_logo_requires_auth(self):
        client = self._get_client()
        resp = client.post(
            f"/api/v1/admin/brands/{self._FAKE_UUID}/logos",
            files={"file": ("logo.png", b"fake", "image/png")},
            data={"logo_type": "main"},
        )
        assert resp.status_code == 401

    def test_update_logo_requires_auth(self):
        client = self._get_client()
        resp = client.put(
            f"/api/v1/admin/brands/{self._FAKE_UUID}/logos/{self._FAKE_UUID}",
            json={"logo_type": "icon"},
        )
        assert resp.status_code == 401

    def test_delete_logo_requires_auth(self):
        client = self._get_client()
        resp = client.delete(
            f"/api/v1/admin/brands/{self._FAKE_UUID}/logos/{self._FAKE_UUID}"
        )
        assert resp.status_code == 401

    def test_download_logo_requires_auth(self):
        client = self._get_client()
        resp = client.get(
            f"/api/v1/admin/brands/{self._FAKE_UUID}/logos/{self._FAKE_UUID}/download"
        )
        assert resp.status_code == 401

    # --- Keywords ---

    def test_list_keywords_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/admin/keywords")
        assert resp.status_code == 401

    def test_create_keyword_requires_auth(self):
        client = self._get_client()
        resp = client.post("/api/v1/admin/keywords", json={
            "word_zh": "球鞋", "word_en": "sneakers",
        })
        assert resp.status_code == 401

    def test_update_keyword_requires_auth(self):
        client = self._get_client()
        resp = client.put(f"/api/v1/admin/keywords/{self._FAKE_UUID}", json={"word_zh": "更新"})
        assert resp.status_code == 401

    def test_delete_keyword_requires_auth(self):
        client = self._get_client()
        resp = client.delete(f"/api/v1/admin/keywords/{self._FAKE_UUID}")
        assert resp.status_code == 401

    # --- Monitor Groups ---

    def test_list_monitor_groups_requires_auth(self):
        client = self._get_client()
        resp = client.get("/api/v1/admin/monitor-groups")
        assert resp.status_code == 401

    def test_update_monitor_group_requires_auth(self):
        client = self._get_client()
        resp = client.put(
            f"/api/v1/admin/monitor-groups/{self._FAKE_UUID}",
            json={"display_name": "更新"},
        )
        assert resp.status_code == 401

    # --- Invalid token ---

    def test_invalid_token_returns_401(self):
        client = self._get_client()
        resp = client.get(
            "/api/v1/admin/sources",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401


class TestFileStorageServiceValidation:
    """Unit tests for FileStorageService validation logic."""

    def _get_service(self):
        from app.services.file_storage_service import FileStorageService
        return FileStorageService()

    def test_validate_valid_png(self):
        svc = self._get_service()
        assert svc.validate_file_format("logo.png") == "png"

    def test_validate_valid_svg(self):
        svc = self._get_service()
        assert svc.validate_file_format("logo.svg") == "svg"

    def test_validate_valid_jpg(self):
        svc = self._get_service()
        assert svc.validate_file_format("logo.jpg") == "jpg"

    def test_validate_jpeg_normalizes_to_jpg(self):
        svc = self._get_service()
        assert svc.validate_file_format("logo.jpeg") == "jpg"

    def test_validate_invalid_format_raises(self):
        from app.utils.errors import ValidationError
        svc = self._get_service()
        with pytest.raises(ValidationError):
            svc.validate_file_format("logo.gif")

    def test_validate_no_extension_raises(self):
        from app.utils.errors import ValidationError
        svc = self._get_service()
        with pytest.raises(ValidationError):
            svc.validate_file_format("logo")

    def test_validate_valid_logo_type(self):
        svc = self._get_service()
        for lt in ("main", "horizontal", "icon", "monochrome", "other"):
            assert svc.validate_logo_type(lt) == lt

    def test_validate_invalid_logo_type_raises(self):
        from app.utils.errors import ValidationError
        svc = self._get_service()
        with pytest.raises(ValidationError):
            svc.validate_logo_type("invalid_type")
