import json

import pytest
from django.test import Client
from django.urls import resolve, reverse


@pytest.mark.django_db
class TestCoreUrls:
    def test_admin_url_resolves(self):
        """Test admin URL resolves correctly"""
        url = reverse("admin:index")
        assert url == "/admin/"

    def test_root_url_resolves_to_index(self):
        """Test root URL resolves to trantrac index"""
        url = reverse("index")
        assert url == "/"
        resolved = resolve(url)
        assert resolved.view_name == "index"

    def test_accounts_login_url_resolves(self):
        """Test accounts login URL resolves"""
        url = "/accounts/login/"
        resolved = resolve(url)
        # Should resolve to allauth login view
        assert resolved.url_name == "account_login"

    def test_users_delete_url_resolves(self):
        """Test users delete URL resolves correctly"""
        url = reverse("users:user_delete")
        assert url == "/users/delete/"

    def test_health_check_returns_200(self):
        """Test /health/ returns 200 without authentication"""
        client = Client()
        response = client.get(reverse("health_check"))
        assert response.status_code == 200

    def test_health_check_returns_json(self):
        """Test /health/ returns JSON with status ok"""
        client = Client()
        response = client.get(reverse("health_check"))
        data = json.loads(response.content)
        assert data == {"status": "ok"}

    def test_health_check_url(self):
        """Test /health/ resolves correctly"""
        url = reverse("health_check")
        assert url == "/health/"
