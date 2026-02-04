import pytest
from django.contrib.messages import get_messages

from tests.conftest import TestCase
from users.models import User


@pytest.mark.django_db
class TestUserDeleteView(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")

    def test_user_delete_requires_login(self):
        """Test user_delete view requires login"""
        response = self.client.get("/users/delete/")
        # Should redirect to login
        assert response.status_code == 302
        assert "/accounts/login" in response.url

    def test_user_delete_get_shows_confirmation_page(self):
        """Test user_delete GET shows confirmation page"""
        self.client.force_login(self.user)
        response = self.client.get("/users/delete/")

        assert response.status_code == 200
        assert b"user" in response.content or response.status_code == 200

    def test_user_delete_post_deletes_user(self):
        """Test user_delete POST deletes the user"""
        user_email = self.user.email
        self.client.force_login(self.user)

        self.client.post("/users/delete/")

        # User should be deleted
        assert not User.objects.filter(email=user_email).exists()

    def test_user_delete_post_shows_success_message(self):
        """Test user_delete POST shows success message"""
        self.client.force_login(self.user)
        response = self.client.post("/users/delete/", follow=True)

        messages = list(get_messages(response.wsgi_request))
        assert any("cancellato con successo" in str(m) for m in messages)
