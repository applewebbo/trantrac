from pathlib import Path

import pytest
from django.conf import settings

from tests.conftest import TestCase


@pytest.mark.django_db
class TestPWAEndpoints(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")

    def test_manifest_json_returns_200(self):
        """manifest.json endpoint returns 200"""
        response = self.client.get("/manifest.json")
        assert response.status_code == 200

    def test_manifest_json_content_type(self):
        """manifest.json has correct content type"""
        response = self.client.get("/manifest.json")
        assert "application/json" in response["Content-Type"]

    def test_manifest_contains_app_name(self):
        """manifest.json contains the configured app name"""
        response = self.client.get("/manifest.json")
        assert b"TranTrac" in response.content

    def test_serviceworker_returns_200(self):
        """serviceworker.js endpoint returns 200"""
        response = self.client.get("/serviceworker.js")
        assert response.status_code == 200

    def test_serviceworker_content_type(self):
        """serviceworker.js has JavaScript content type"""
        response = self.client.get("/serviceworker.js")
        assert "javascript" in response["Content-Type"]

    def test_offline_page_returns_200(self):
        """Offline page returns 200"""
        response = self.client.get("/offline/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestPWAMetaTags(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")

    def _get_index(self):
        with self.login(username=self.user.email, password="password"):
            return self.get("index")

    def test_manifest_link_in_head(self):
        """base.html includes manifest link tag"""
        response = self._get_index()
        self.assertContains(response, 'rel="manifest"')

    def test_theme_color_meta_in_head(self):
        """base.html includes theme-color meta tag"""
        response = self._get_index()
        self.assertContains(response, 'name="theme-color"')

    def test_serviceworker_registration_script(self):
        """base.html includes service worker registration script"""
        response = self._get_index()
        self.assertContains(response, "serviceWorker")


class TestPWAIcons:
    def test_icon_192_exists(self):
        """192x192 PWA icon file exists"""
        icon_path = (
            Path(settings.BASE_DIR) / "static" / "images" / "icons" / "icon-192x192.png"
        )
        assert icon_path.exists(), f"Missing: {icon_path}"

    def test_icon_512_exists(self):
        """512x512 PWA icon file exists"""
        icon_path = (
            Path(settings.BASE_DIR) / "static" / "images" / "icons" / "icon-512x512.png"
        )
        assert icon_path.exists(), f"Missing: {icon_path}"

    def test_icon_192_is_valid_png(self):
        """192x192 icon is a valid PNG file"""
        icon_path = (
            Path(settings.BASE_DIR) / "static" / "images" / "icons" / "icon-192x192.png"
        )
        assert icon_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    def test_icon_512_is_valid_png(self):
        """512x512 icon is a valid PNG file"""
        icon_path = (
            Path(settings.BASE_DIR) / "static" / "images" / "icons" / "icon-512x512.png"
        )
        assert icon_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


class TestPWASettings:
    def test_pwa_in_installed_apps(self):
        """pwa app is in INSTALLED_APPS"""
        assert "pwa" in settings.INSTALLED_APPS

    def test_pwa_app_name_configured(self):
        """PWA_APP_NAME is configured"""
        assert settings.PWA_APP_NAME == "TranTrac"

    def test_pwa_app_lang_is_italian(self):
        """PWA_APP_LANG is set to Italian"""
        assert settings.PWA_APP_LANG == "it-IT"

    def test_pwa_service_worker_path_exists(self):
        """PWA_SERVICE_WORKER_PATH points to an existing file"""
        sw_path = Path(settings.PWA_SERVICE_WORKER_PATH)
        assert sw_path.exists(), f"Missing service worker: {sw_path}"

    def test_pwa_debug_mode_off_in_production(self):
        """PWA_APP_DEBUG_MODE is False in production"""
        assert settings.PWA_APP_DEBUG_MODE is False
