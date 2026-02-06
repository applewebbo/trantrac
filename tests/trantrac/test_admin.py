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
