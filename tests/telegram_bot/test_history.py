from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asgiref.sync import sync_to_async

from telegram_bot.handlers.history import (
    handle_delete_callback,
    handle_recent_transactions,
)
from telegram_bot.models import BotTransaction
from tests.conftest import TestCase
from trantrac.models import Account, Category, Subcategory


def _make_update(chat_id=12345):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.callback_query = None
    update.message.reply_text = AsyncMock()
    return update


def _make_context():
    context = MagicMock()
    context.user_data = {}
    return context


@pytest.mark.django_db
class TestHandleRecentTransactions(TestCase):
    def setUp(self):
        self.user = self.make_user("history@example.com")
        self.user.telegram_chat_id = 12345
        self.user.telegram_status = "approved"
        self.user.save()
        self.category = Category.objects.create(name="Food")
        self.subcategory = Subcategory.objects.create(
            name="Bar", category=self.category, skip_sheet_save=True
        )
        self.account = Account.objects.create(name="Test User")

    async def _make_bot_tx(self, description="caffè", amount="10.00"):
        return await sync_to_async(BotTransaction.objects.create)(
            user=self.user,
            amount=amount,
            description=description,
            category=self.category,
            subcategory=self.subcategory,
            account=self.account,
            date=date.today(),
            telegram_message_id=1,
        )

    async def test_unauthenticated_user(self):
        """Unknown chat_id gets an error message."""
        update = _make_update(chat_id=99999)
        await handle_recent_transactions(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "non collegato" in text

    async def test_no_transactions(self):
        """Authenticated user with no transactions gets informative message."""
        update = _make_update()
        await handle_recent_transactions(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "Nessuna transazione" in text

    async def test_shows_transactions(self):
        """Transactions are listed with amount, description and category."""
        await self._make_bot_tx(description="caffè", amount="3.50")
        await self._make_bot_tx(description="benzina", amount="60.00")
        update = _make_update()
        await handle_recent_transactions(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "caffè" in text
        assert "benzina" in text
        assert "Food" in text
        assert "Bar" in text

    async def test_inline_keyboard_has_delete_buttons(self):
        """Each transaction has a delete inline button with bot_id in callback_data."""
        tx = await self._make_bot_tx()
        update = _make_update()
        await handle_recent_transactions(update, _make_context())
        kwargs = update.message.reply_text.call_args[1]
        markup = kwargs["reply_markup"]
        buttons = [btn for row in markup.inline_keyboard for btn in row]
        assert len(buttons) == 1
        assert buttons[0].callback_data == f"delete:{tx.bot_id}"

    async def test_shows_at_most_five(self):
        """At most 5 transactions are shown even if more exist in DB."""
        for i in range(7):
            await self._make_bot_tx(description=f"tx{i}")
        update = _make_update()
        await handle_recent_transactions(update, _make_context())
        kwargs = update.message.reply_text.call_args[1]
        markup = kwargs["reply_markup"]
        buttons = [btn for row in markup.inline_keyboard for btn in row]
        assert len(buttons) == 5


def _make_callback_update(chat_id=12345, callback_data="delete:AAAABBBB-BOT"):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.edit_message_reply_markup = AsyncMock()
    update.callback_query.message = MagicMock()
    update.callback_query.message.reply_text = AsyncMock()
    update.callback_query.data = callback_data
    return update


@pytest.mark.django_db
class TestHandleDeleteCallback(TestCase):
    def setUp(self):
        self.user = self.make_user("del@example.com")
        self.user.telegram_chat_id = 12345
        self.user.telegram_status = "approved"
        self.user.save()
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Bar", category=category, skip_sheet_save=True
        )
        account = Account.objects.create(name="Test")
        self.tx = BotTransaction.objects.create(
            user=self.user,
            amount="10.00",
            description="caffè",
            category=category,
            subcategory=subcategory,
            account=account,
            date=date.today(),
            telegram_message_id=1,
        )

    async def test_unauthenticated_user(self):
        """Unknown chat_id gets error message."""
        update = _make_callback_update(chat_id=99999)
        await handle_delete_callback(update, _make_context())
        update.callback_query.edit_message_text.assert_awaited_once()
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "non collegato" in text

    async def test_delete_shows_confirmation_buttons(self):
        """'delete:<bot_id>' callback replaces markup with confirm/cancel buttons."""
        update = _make_callback_update(callback_data=f"delete:{self.tx.bot_id}")
        await handle_delete_callback(update, _make_context())
        update.callback_query.edit_message_reply_markup.assert_awaited_once()
        markup = update.callback_query.edit_message_reply_markup.call_args[1][
            "reply_markup"
        ]
        button_datas = [
            btn.callback_data for row in markup.inline_keyboard for btn in row
        ]
        assert f"confirm_delete:{self.tx.bot_id}" in button_datas
        assert "cancel_delete" in button_datas

    @patch("telegram_bot.handlers.history.delete_bot_transaction")
    async def test_confirm_delete_success(self, mock_delete):
        """confirm_delete calls service and shows success message."""
        mock_delete.return_value = (True, "✅ Eliminato: 10€ — caffè")
        update = _make_callback_update(callback_data=f"confirm_delete:{self.tx.bot_id}")
        await handle_delete_callback(update, _make_context())
        mock_delete.assert_called_once()
        update.callback_query.edit_message_text.assert_awaited_once_with(
            "✅ Eliminato: 10€ — caffè"
        )

    @patch("telegram_bot.handlers.history.delete_bot_transaction")
    async def test_confirm_delete_failure(self, mock_delete):
        """confirm_delete shows error message on service failure."""
        mock_delete.return_value = (
            False,
            "❌ Errore nella cancellazione da Google Sheets.",
        )
        update = _make_callback_update(callback_data=f"confirm_delete:{self.tx.bot_id}")
        await handle_delete_callback(update, _make_context())
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Errore" in text

    async def test_cancel_delete(self):
        """cancel_delete removes markup and sends cancellation notice."""
        update = _make_callback_update(callback_data="cancel_delete")
        await handle_delete_callback(update, _make_context())
        update.callback_query.edit_message_reply_markup.assert_awaited_once_with(
            reply_markup=None
        )
        update.callback_query.message.reply_text.assert_awaited_once()
        text = update.callback_query.message.reply_text.call_args[0][0]
        assert "annullata" in text
