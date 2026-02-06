from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest

from telegram_bot.models import PendingTransaction
from telegram_bot.services.transaction_service import create_transaction
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
