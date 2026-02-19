"""Tests for the admin CSV upload handler."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from telegram_bot.handlers.csv_upload import handle_csv_upload
from tests.conftest import TestCase
from users.models import User


def _make_update(chat_id=12345, file_name="transactions.csv"):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.callback_query = None
    update.message.reply_text = AsyncMock()
    update.message.document = MagicMock()
    update.message.document.file_name = file_name
    update.message.document.file_id = "fake-file-id"
    return update


def _make_context():
    mock_file = MagicMock()
    mock_file.download_to_memory = AsyncMock()
    context = MagicMock()
    context.bot.get_file = AsyncMock(return_value=mock_file)
    return context


@pytest.mark.django_db
class TestHandleCsvUpload(TestCase):
    def setUp(self):
        self.admin = self.make_user("admin@example.com")
        self.admin.telegram_chat_id = 11111
        self.admin.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.admin.is_staff = True
        self.admin.save()

        self.regular = self.make_user("regular@example.com")
        self.regular.telegram_chat_id = 22222
        self.regular.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.regular.save()

        self.pending = self.make_user("pending@example.com")
        self.pending.telegram_chat_id = 33333
        self.pending.telegram_status = User.TELEGRAM_STATUS_PENDING
        self.pending.save()

    async def test_unenrolled_user_gets_auth_message(self):
        update = _make_update(chat_id=99999)
        await handle_csv_upload(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "non collegato" in text

    async def test_pending_user_gets_awaiting_message(self):
        update = _make_update(chat_id=33333)
        await handle_csv_upload(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "attesa" in text

    async def test_regular_user_gets_forbidden_message(self):
        update = _make_update(chat_id=22222)
        await handle_csv_upload(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "admin" in text.lower()

    async def test_non_csv_file_gets_error(self):
        update = _make_update(chat_id=11111, file_name="data.xlsx")
        await handle_csv_upload(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert ".csv" in text

    @patch("telegram_bot.handlers.csv_upload.import_csv_to_sheet")
    async def test_admin_csv_success(self, mock_import):
        mock_import.return_value = (True, "File importato con successo")
        update = _make_update(chat_id=11111)
        await handle_csv_upload(update, _make_context())

        mock_import.assert_called_once()
        calls = update.message.reply_text.await_args_list
        assert len(calls) == 2
        final_text = calls[1][0][0]
        assert "✅" in final_text
        assert "successo" in final_text

    @patch("telegram_bot.handlers.csv_upload.import_csv_to_sheet")
    async def test_admin_csv_failure(self, mock_import):
        mock_import.return_value = (False, "Ops, qualcosa è andato storto..")
        update = _make_update(chat_id=11111)
        await handle_csv_upload(update, _make_context())

        calls = update.message.reply_text.await_args_list
        final_text = calls[1][0][0]
        assert "❌" in final_text

    @patch("telegram_bot.handlers.csv_upload.import_csv_to_sheet")
    async def test_exception_shows_generic_error(self, mock_import):
        mock_import.side_effect = Exception("connection error")
        update = _make_update(chat_id=11111)
        await handle_csv_upload(update, _make_context())

        calls = update.message.reply_text.await_args_list
        final_text = calls[1][0][0]
        assert "Errore" in final_text
