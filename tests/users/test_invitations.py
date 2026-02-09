import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext as _

User = get_user_model()


@pytest.mark.django_db
class TestInvitationIntegration:
    """Test django-invitations integration with project"""

    def test_invitations_installed(self):
        """Test that invitations app is installed"""
        assert "invitations" in settings.INSTALLED_APPS

    def test_invitation_only_enabled(self):
        """Test that INVITATION_ONLY setting is enabled"""
        assert settings.INVITATIONS_INVITATION_ONLY is True

    def test_invitations_adapter_configured(self):
        """Test that InvitationsAdapter is configured"""
        assert settings.ACCOUNT_ADAPTER == "invitations.models.InvitationsAdapter"

    def test_public_signup_disabled(self, client):
        """Test that signup without invitation is blocked"""
        signup_url = reverse("account_signup")
        client.post(
            signup_url,
            {
                "email": "unauthorized@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )
        # User should NOT be created without invitation
        assert not User.objects.filter(email="unauthorized@example.com").exists()

    def test_invitations_urls_configured(self):
        """Test that invitations URLs are accessible"""
        # Test that the invitations namespace exists
        url = reverse("invitations:send-invite")
        assert url == "/invitations/send-invite/"

    def test_admin_invitation_access(self, test_user, client):
        """Test that admin can access invitation management"""
        test_user.is_staff = True
        test_user.is_superuser = True
        test_user.save()

        client.force_login(test_user)

        # Access admin invitations page
        admin_url = reverse("admin:invitations_invitation_changelist")
        response = client.get(admin_url)
        assert response.status_code == 200

    def test_italian_translations_loaded(self):
        """Test that Italian translations are loaded correctly"""
        # Test a few key translations from django-invitations
        assert _("E-mail") == "Email"
        assert _("Invite") == "Invita"
        # Note: translations are context-dependent and may require activation
