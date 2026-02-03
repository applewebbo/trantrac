import pytest
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
