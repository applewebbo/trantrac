import pytest
from django.utils import timezone

from telegram_bot.models import (
    BotTransaction,
    CategoryKeyword,
    PendingTransaction,
    TelegramAuthSession,
    generate_bot_id,
)
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


class TestGenerateBotId:
    def test_format(self):
        """Test bot_id format is XXXXXXXX-BOT"""
        bot_id = generate_bot_id()
        assert bot_id.endswith("-BOT")
        assert len(bot_id) == 12  # 8 hex chars + -BOT (4)
        assert bot_id[:8].isupper()
        assert all(c in "0123456789ABCDEF" for c in bot_id[:8])

    def test_uniqueness(self):
        """Test that generate_bot_id produces unique values"""
        ids = {generate_bot_id() for _ in range(100)}
        assert len(ids) == 100


@pytest.mark.django_db
class TestBotTransaction(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")
        self.category = Category.objects.create(name="Food")
        self.subcategory = Subcategory.objects.create(
            name="Groceries", category=self.category, skip_sheet_save=True
        )
        self.account = Account.objects.create(name="Main")

    def _make_bot_tx(self, **kwargs):
        defaults = dict(
            user=self.user,
            amount="10.00",
            description="test",
            category=self.category,
            subcategory=self.subcategory,
            account=self.account,
            date=timezone.now().date(),
            telegram_message_id=1,
        )
        defaults.update(kwargs)
        return BotTransaction.objects.create(**defaults)

    def test_str_representation(self):
        tx = self._make_bot_tx(amount="50.00", description="caffè")
        assert tx.bot_id in str(tx)
        assert "50" in str(tx)
        assert "caffè" in str(tx)

    def test_bot_id_auto_generated(self):
        tx = self._make_bot_tx()
        assert tx.bot_id.endswith("-BOT")
        assert len(tx.bot_id) == 12

    def test_bot_id_unique(self):
        tx1 = self._make_bot_tx()
        tx2 = self._make_bot_tx()
        assert tx1.bot_id != tx2.bot_id

    def test_ordering_newest_first(self):
        tx1 = self._make_bot_tx(description="first")
        tx2 = self._make_bot_tx(description="second")
        qs = list(BotTransaction.objects.filter(user=self.user))
        assert qs[0] == tx2
        assert qs[1] == tx1
