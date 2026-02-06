import pytest
from django.contrib.admin.sites import AdminSite
from django.utils import timezone

from telegram_bot.admin import TelegramAuthSessionAdmin
from telegram_bot.models import TelegramAuthSession
from tests.conftest import TestCase


@pytest.mark.django_db
class TestTelegramAuthSessionAdmin(TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = TelegramAuthSessionAdmin(TelegramAuthSession, self.site)
        self.user = self.make_user("admin@example.com")

    def test_is_expired_display_not_expired(self):
        """Test is_expired display method for non-expired session"""
        session = TelegramAuthSession.objects.create(
            chat_id=12345, phone_number="+1234567890"
        )

        # Session just created, should not be expired
        assert self.admin.is_expired(session) is False

    def test_is_expired_display_expired(self):
        """Test is_expired display method for expired session"""
        session = TelegramAuthSession.objects.create(
            chat_id=12345, phone_number="+1234567890"
        )

        # Manually set created_at to 10 minutes ago
        session.created_at = timezone.now() - timezone.timedelta(minutes=10)
        session.save()

        # Session should be expired
        assert self.admin.is_expired(session) is True
