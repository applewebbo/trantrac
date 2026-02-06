import pytest
from django.utils import timezone

from telegram_bot.models import CategoryKeyword, PendingTransaction, TelegramAuthSession
from tests.conftest import TestCase
from trantrac.models import Account, Category, Subcategory


@pytest.mark.django_db
class TestTelegramAuthSession(TestCase):
    def test_is_expired_not_expired(self):
        """Test is_expired returns False for recent session"""
        session = TelegramAuthSession.objects.create(
            chat_id=12345, phone_number="+1234567890"
        )

        # Session just created, should not be expired (< 5 minutes)
        assert session.is_expired() is False

    def test_is_expired_expired(self):
        """Test is_expired returns True for old session"""
        session = TelegramAuthSession.objects.create(
            chat_id=12345, phone_number="+1234567890"
        )

        # Set created_at to 10 minutes ago (> 5 minutes)
        session.created_at = timezone.now() - timezone.timedelta(minutes=10)
        session.save()

        assert session.is_expired() is True

    def test_str_representation(self):
        """Test __str__ method"""
        session = TelegramAuthSession.objects.create(
            chat_id=12345, phone_number="+1234567890"
        )
        assert str(session) == "Chat 12345 - +1234567890"


@pytest.mark.django_db
class TestPendingTransaction(TestCase):
    def test_str_representation(self):
        """Test __str__ method"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )
        account = Account.objects.create(name="Main")

        transaction = PendingTransaction.objects.create(
            user=user,
            amount=100.50,
            description="Test transaction",
            category=category,
            subcategory=subcategory,
            account=account,
            date=timezone.now().date(),
            telegram_message_id=123456,
            status="pending",
        )

        # Decimal representation drops trailing zeros
        expected = f"{user} - 100.5€ - pending"
        assert str(transaction) == expected


@pytest.mark.django_db
class TestCategoryKeyword(TestCase):
    def test_str_representation(self):
        """Test __str__ method"""
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )

        keyword = CategoryKeyword.objects.create(
            keyword="spesa", subcategory=subcategory, priority=1
        )

        assert str(keyword) == "spesa → Groceries"
