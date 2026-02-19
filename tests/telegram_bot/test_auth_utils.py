"""Tests for telegram_bot.utils.auth helpers."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_bot.utils.auth import get_approved_user, reply_if_not_enrolled
from tests.conftest import TestCase
from users.models import User


def _make_message_update(chat_id=12345):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.callback_query = None
    update.message.reply_text = AsyncMock()
    return update


def _make_callback_update(chat_id=12345):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.callback_query = MagicMock()
    update.callback_query.edit_message_text = AsyncMock()
    return update


@pytest.mark.django_db
class TestGetApprovedUser(TestCase):
    def setUp(self):
        self.approved = self.make_user("approved@example.com")
        self.approved.telegram_chat_id = 11111
        self.approved.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.approved.save()

        self.pending = self.make_user("pending@example.com")
        self.pending.telegram_chat_id = 22222
        self.pending.telegram_status = User.TELEGRAM_STATUS_PENDING
        self.pending.save()

        self.null_status = self.make_user("null@example.com")
        self.null_status.telegram_chat_id = 33333
        self.null_status.telegram_status = None
        self.null_status.save()

    async def test_returns_user_when_approved(self):
        result = await get_approved_user(_make_message_update(chat_id=11111))
        assert result is not None
        assert result.email == "approved@example.com"

    async def test_returns_none_when_pending(self):
        result = await get_approved_user(_make_message_update(chat_id=22222))
        assert result is None

    async def test_returns_none_when_status_null(self):
        result = await get_approved_user(_make_message_update(chat_id=33333))
        assert result is None

    async def test_returns_none_for_unknown_chat_id(self):
        result = await get_approved_user(_make_message_update(chat_id=99999))
        assert result is None


@pytest.mark.django_db
class TestReplyIfNotEnrolled(TestCase):
    def setUp(self):
        self.approved = self.make_user("approved2@example.com")
        self.approved.telegram_chat_id = 44444
        self.approved.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.approved.save()

        self.pending = self.make_user("pending2@example.com")
        self.pending.telegram_chat_id = 55555
        self.pending.telegram_status = User.TELEGRAM_STATUS_PENDING
        self.pending.save()

    async def test_returns_false_for_approved_user(self):
        update = _make_message_update(chat_id=44444)
        result = await reply_if_not_enrolled(update)
        assert result is False
        update.message.reply_text.assert_not_awaited()

    async def test_returns_true_for_unknown_user(self):
        update = _make_message_update(chat_id=99999)
        result = await reply_if_not_enrolled(update)
        assert result is True
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "non collegato" in text

    async def test_returns_true_for_pending_user(self):
        update = _make_message_update(chat_id=55555)
        result = await reply_if_not_enrolled(update)
        assert result is True
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "attesa" in text

    async def test_uses_edit_message_for_callback_pending(self):
        """Callback query context uses edit_message_text instead of reply_text."""
        update = _make_callback_update(chat_id=55555)
        result = await reply_if_not_enrolled(update)
        assert result is True
        update.callback_query.edit_message_text.assert_awaited_once()
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "attesa" in text

    async def test_unknown_user_callback_uses_edit_message(self):
        """Unknown user in callback context gets edit_message_text."""
        update = _make_callback_update(chat_id=99999)
        result = await reply_if_not_enrolled(update)
        assert result is True
        update.callback_query.edit_message_text.assert_awaited_once()
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "non collegato" in text
