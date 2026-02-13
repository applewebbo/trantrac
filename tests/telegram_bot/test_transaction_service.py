from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from telegram_bot.models import BotTransaction, PendingTransaction
from telegram_bot.services.transaction_service import (
    BOT_TRANSACTIONS_LIMIT,
    _prune_bot_transactions,
    create_transaction,
    delete_bot_transaction,
)
from tests.conftest import TestCase
from trantrac.models import Account, Category, CategoryUsage, Subcategory


@pytest.mark.django_db
class TestCreateTransaction(TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.user = self.make_user("test@example.com")
        self.user.display_name = "Test User"
        self.user.save()
        self.category = Category.objects.create(name="Food")
        self.subcategory = Subcategory.objects.create(
            name="Groceries", category=self.category, skip_sheet_save=True
        )

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_success(self, mock_save):
        """Test successful transaction creation"""
        mock_save.return_value = True

        success, message = create_transaction(
            user=self.user,
            amount=Decimal("50.00"),
            description="Test transaction",
            subcategory=self.subcategory,
            telegram_message_id=12345,
        )

        assert success is True
        assert "✅ Salvato" in message
        assert "50" in message
        assert "Test transaction" in message

        # Verify save_to_sheet was called
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0]
        assert call_args[1] == "USCITE"

        # Verify CategoryUsage was created
        assert CategoryUsage.objects.filter(user=self.user).count() == 1

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_with_date(self, mock_save):
        """Test transaction creation with specific date"""
        mock_save.return_value = True
        specific_date = date(2025, 1, 15)

        success, message = create_transaction(
            user=self.user,
            amount=Decimal("75.50"),
            description="Test transaction",
            subcategory=self.subcategory,
            telegram_message_id=12345,
            transaction_date=specific_date,
        )

        assert success is True
        # Verify date format in values
        call_args = mock_save.call_args[0]
        values = call_args[0]
        assert "15/01/2025" in values[0]  # DD/MM/YYYY format

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_creates_account(self, mock_save):
        """Test transaction creates account if it doesn't exist"""
        mock_save.return_value = True

        # Ensure no account exists
        Account.objects.all().delete()

        success, message = create_transaction(
            user=self.user,
            amount=Decimal("50.00"),
            description="Test transaction",
            subcategory=self.subcategory,
            telegram_message_id=12345,
        )

        assert success is True
        # Verify account was created
        assert Account.objects.filter(name="Test User").exists()

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_failure_creates_pending(self, mock_save):
        """Test transaction failure creates PendingTransaction"""
        # Simulate save failure
        mock_save.side_effect = Exception("API Error")

        success, message = create_transaction(
            user=self.user,
            amount=Decimal("50.00"),
            description="Test transaction",
            subcategory=self.subcategory,
            telegram_message_id=12345,
        )

        assert success is False
        assert "⚠️ Errore" in message
        assert "ritentata automaticamente" in message

        # Verify PendingTransaction was created
        pending = PendingTransaction.objects.filter(user=self.user).first()
        assert pending is not None
        assert pending.amount == Decimal("50.00")
        assert pending.description == "Test transaction"
        assert pending.status == "pending"
        assert "API Error" in pending.last_error

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_formats_amount_italian(self, mock_save):
        """Test transaction formats amount with Italian comma"""
        mock_save.return_value = True

        create_transaction(
            user=self.user,
            amount=Decimal("125.50"),
            description="Test transaction",
            subcategory=self.subcategory,
            telegram_message_id=12345,
        )

        # Verify amount is formatted with comma
        call_args = mock_save.call_args[0]
        values = call_args[0]
        assert "125,50" in values[0]  # Italian format with comma

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_uses_email_if_empty_display_name(self, mock_save):
        """Test transaction uses email when display_name is empty"""
        mock_save.return_value = True
        user_no_name = self.make_user("noname@example.com")
        user_no_name.display_name = ""
        user_no_name.save()

        create_transaction(
            user=user_no_name,
            amount=Decimal("50.00"),
            description="Test transaction",
            subcategory=self.subcategory,
            telegram_message_id=12345,
        )

        # Verify email is used in values when display_name is empty
        call_args = mock_save.call_args[0]
        values = call_args[0]
        assert "noname@example.com" in values[0]

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_saves_bot_transaction(self, mock_save):
        """Test successful transaction saves a BotTransaction record"""
        mock_save.return_value = True

        success, _ = create_transaction(
            user=self.user,
            amount=Decimal("50.00"),
            description="caffè",
            subcategory=self.subcategory,
            telegram_message_id=999,
        )

        assert success is True
        bt = BotTransaction.objects.filter(user=self.user).first()
        assert bt is not None
        assert bt.amount == Decimal("50.00")
        assert bt.description == "caffè"
        assert bt.bot_id.startswith("BOT-")

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_includes_bot_id_in_sheet_values(self, mock_save):
        """Test that bot_id is passed as 8th column to Google Sheets"""
        mock_save.return_value = True

        create_transaction(
            user=self.user,
            amount=Decimal("30.00"),
            description="test",
            subcategory=self.subcategory,
            telegram_message_id=1,
        )

        call_args = mock_save.call_args[0]
        row = call_args[0][0]
        assert len(row) == 8
        assert row[7].startswith("BOT-")

    @patch("telegram_bot.services.transaction_service.save_to_sheet")
    def test_create_transaction_failure_does_not_save_bot_transaction(self, mock_save):
        """Test that BotTransaction is NOT created when Sheets save fails"""
        mock_save.side_effect = Exception("API Error")

        success, _ = create_transaction(
            user=self.user,
            amount=Decimal("50.00"),
            description="test",
            subcategory=self.subcategory,
            telegram_message_id=1,
        )

        assert success is False
        assert BotTransaction.objects.filter(user=self.user).count() == 0


@pytest.mark.django_db
class TestPruneBotTransactions(TestCase):
    def setUp(self):
        self.user = self.make_user("prune@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )
        account = Account.objects.create(name="Main")
        self.defaults = dict(
            user=self.user,
            amount="10.00",
            description="x",
            category=category,
            subcategory=subcategory,
            account=account,
            date=date.today(),
            telegram_message_id=1,
        )

    def _make_bot_tx(self):
        return BotTransaction.objects.create(**self.defaults)

    def test_prune_keeps_exactly_limit(self):
        """Pruning after 6 inserts keeps only 5"""
        for _ in range(BOT_TRANSACTIONS_LIMIT + 1):
            self._make_bot_tx()

        _prune_bot_transactions(self.user)

        assert (
            BotTransaction.objects.filter(user=self.user).count()
            == BOT_TRANSACTIONS_LIMIT
        )

    def test_prune_keeps_newest(self):
        """Pruning retains the most recent transactions"""
        txs = [self._make_bot_tx() for _ in range(BOT_TRANSACTIONS_LIMIT + 1)]
        oldest = txs[0]

        _prune_bot_transactions(self.user)

        assert not BotTransaction.objects.filter(id=oldest.id).exists()

    def test_prune_no_op_when_under_limit(self):
        """Pruning does nothing when count <= limit"""
        for _ in range(3):
            self._make_bot_tx()

        _prune_bot_transactions(self.user)

        assert BotTransaction.objects.filter(user=self.user).count() == 3

    def test_prune_does_not_affect_other_users(self):
        """Pruning only deletes transactions of the target user"""
        other_user = self.make_user("other@example.com")
        for _ in range(BOT_TRANSACTIONS_LIMIT + 1):
            self._make_bot_tx()
        BotTransaction.objects.create(**{**self.defaults, "user": other_user})

        _prune_bot_transactions(self.user)

        assert BotTransaction.objects.filter(user=other_user).count() == 1


@pytest.mark.django_db
class TestDeleteBotTransaction(TestCase):
    def setUp(self):
        self.user = self.make_user("del@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Bar", category=category, skip_sheet_save=True
        )
        account = Account.objects.create(name="Del User")
        self.tx = BotTransaction.objects.create(
            user=self.user,
            amount="25.00",
            description="spritz",
            category=category,
            subcategory=subcategory,
            account=account,
            date=date.today(),
            telegram_message_id=1,
        )

    @patch("telegram_bot.services.transaction_service.delete_row_by_identifier")
    def test_delete_success(self, mock_delete_row):
        """Successful deletion removes from Sheets then DB."""
        mock_delete_row.return_value = True

        success, message = delete_bot_transaction(self.user, self.tx.bot_id)

        assert success is True
        assert "Eliminato" in message
        assert "spritz" in message
        mock_delete_row.assert_called_once_with("USCITE", self.tx.bot_id, 7)
        assert not BotTransaction.objects.filter(id=self.tx.id).exists()

    @patch("telegram_bot.services.transaction_service.delete_row_by_identifier")
    def test_delete_sheets_failure_keeps_db_record(self, mock_delete_row):
        """If Sheets deletion fails, the DB record is kept."""
        mock_delete_row.side_effect = Exception("Sheets error")

        success, message = delete_bot_transaction(self.user, self.tx.bot_id)

        assert success is False
        assert "Google Sheets" in message
        assert BotTransaction.objects.filter(id=self.tx.id).exists()

    def test_delete_not_found(self):
        """Returns error when bot_id does not exist for user."""
        success, message = delete_bot_transaction(self.user, "BOT-NOTEXIST")

        assert success is False
        assert "non trovata" in message

    @patch("telegram_bot.services.transaction_service.delete_row_by_identifier")
    def test_delete_other_user_cannot_delete(self, mock_delete_row):
        """A different user cannot delete another user's transaction."""
        other = self.make_user("other@example.com")

        success, message = delete_bot_transaction(other, self.tx.bot_id)

        assert success is False
        mock_delete_row.assert_not_called()
        assert BotTransaction.objects.filter(id=self.tx.id).exists()
