import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from tests.conftest import TestCase
from trantrac.admin import GoogleSheetsSettingsAdmin
from trantrac.models import GoogleSheetsSettings


@pytest.mark.django_db
class TestGoogleSheetsSettingsAdmin(TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = GoogleSheetsSettingsAdmin(GoogleSheetsSettings, self.site)
        self.user = self.make_user("admin@example.com")
        self.factory = RequestFactory()

    def test_has_add_permission_when_no_settings_exist(self):
        """Test has_add_permission returns True when no settings exist"""
        # Ensure no settings exist
        GoogleSheetsSettings.objects.all().delete()

        request = self.factory.get("/admin/")
        request.user = self.user
        assert self.admin.has_add_permission(request) is True

    def test_has_add_permission_when_settings_exist(self):
        """Test has_add_permission returns False when settings already exist"""
        # Create settings
        GoogleSheetsSettings.objects.create(
            spreadsheet_id="test-id",
            project_id="test-project",
            private_key_id="test-key",
            private_key="test-private-key",
            client_email="test@example.com",
            client_id="123",
            client_x509_cert_url="https://example.com",
        )

        request = self.factory.get("/admin/")
        request.user = self.user
        assert self.admin.has_add_permission(request) is False

    def test_has_delete_permission(self):
        """Test has_delete_permission always returns False"""
        request = self.factory.get("/admin/")
        request.user = self.user

        # Without obj
        assert self.admin.has_delete_permission(request) is False

        # With obj
        settings = GoogleSheetsSettings.get_settings()
        assert self.admin.has_delete_permission(request, settings) is False


class TestAdminAppListReorganization:
    """Test the custom get_app_list that groups report models into a 'Report' section."""

    def test_no_report_models_skips_report_section(self):
        from django.contrib.admin import AdminSite
        from trantrac.admin import _get_app_list_with_report_section

        site = AdminSite()
        # Simulate app list with no report models
        fake_app_list = [
            {
                "name": "Trantrac",
                "app_label": "trantrac",
                "app_url": "/admin/trantrac/",
                "has_module_perms": True,
                "models": [{"object_name": "Category", "name": "Categories"}],
            }
        ]

        from unittest.mock import patch

        with patch("trantrac.admin._original_get_app_list", return_value=fake_app_list):
            result = _get_app_list_with_report_section(site, None)

        app_labels = [app["app_label"] for app in result]
        assert "report" not in app_labels
