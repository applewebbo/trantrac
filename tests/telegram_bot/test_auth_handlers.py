"""Tests for Telegram bot authentication handlers."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from telegram_bot.handlers.auth import (
    handle_contact,
    handle_email_message,
    handle_enrollment_approval,
    handle_start,
)
from telegram_bot.models import TelegramAuthSession
from tests.conftest import TestCase
from users.models import User


def _make_update(chat_id=12345, text=None):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.message.reply_text = AsyncMock()
    update.message.text = text
    update.message.contact = None
    return update


def _make_context():
    context = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


def _make_callback_update(chat_id=12345, callback_data="approve_enrollment:1"):
    update = MagicMock()
    update.effective_chat.id = chat_id
    update.callback_query = MagicMock()
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.data = callback_data
    return update


@pytest.mark.django_db
class TestHandleStart(TestCase):
    def setUp(self):
        self.approved = self.make_user("approved@example.com")
        self.approved.telegram_chat_id = 11111
        self.approved.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.approved.save()

        self.approved_admin = self.make_user("admin@example.com")
        self.approved_admin.telegram_chat_id = 22222
        self.approved_admin.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.approved_admin.is_staff = True
        self.approved_admin.save()

        self.pending = self.make_user("pending@example.com")
        self.pending.telegram_chat_id = 33333
        self.pending.telegram_status = User.TELEGRAM_STATUS_PENDING
        self.pending.save()

    async def test_approved_regular_user_sees_welcome(self):
        update = _make_update(chat_id=11111)
        await handle_start(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "Sei già collegato" in text
        assert "csv" not in text.lower()

    async def test_approved_admin_sees_admin_welcome(self):
        update = _make_update(chat_id=22222)
        await handle_start(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "admin" in text.lower()
        assert "csv" in text.lower()

    async def test_pending_user_sees_awaiting_message(self):
        update = _make_update(chat_id=33333)
        await handle_start(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "attesa" in text

    async def test_unknown_user_gets_phone_request(self):
        update = _make_update(chat_id=99999)
        await handle_start(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        kwargs = update.message.reply_text.call_args[1]
        assert "reply_markup" in kwargs


@pytest.mark.django_db
class TestHandleContact(TestCase):
    async def test_creates_auth_session(self):
        update = _make_update(chat_id=12345)
        update.message.contact = MagicMock(phone_number="+39123456789")
        await handle_contact(update, _make_context())
        session = await TelegramAuthSession.objects.filter(chat_id=12345).afirst()
        assert session is not None
        assert session.phone_number == "+39123456789"
        update.message.reply_text.assert_awaited_once()

    async def test_no_contact_returns_error(self):
        update = _make_update(chat_id=12345)
        update.message.contact = None
        await handle_contact(update, _make_context())
        update.message.reply_text.assert_awaited_once()
        text = update.message.reply_text.call_args[0][0]
        assert "non valido" in text


@pytest.mark.django_db
class TestHandleEmailMessage(TestCase):
    def setUp(self):
        self.regular_user = self.make_user("regular@example.com")
        self.regular_user.display_name = "Mario"
        self.regular_user.save()

        self.staff_user = self.make_user("staff@example.com")
        self.staff_user.is_staff = True
        self.staff_user.display_name = "Admin"
        self.staff_user.save()

        self.admin_linked = self.make_user("adminlinked@example.com")
        self.admin_linked.telegram_chat_id = 55555
        self.admin_linked.telegram_status = User.TELEGRAM_STATUS_APPROVED
        self.admin_linked.is_staff = True
        self.admin_linked.save()

        TelegramAuthSession.objects.create(chat_id=12345, phone_number="+39111222333")

    async def test_no_session_returns_error(self):
        update = _make_update(chat_id=99999, text="regular@example.com")
        await handle_email_message(update, _make_context())
        text = update.message.reply_text.call_args[0][0]
        assert "Sessione" in text

    async def test_email_not_found_returns_error(self):
        update = _make_update(chat_id=12345, text="unknown@example.com")
        await handle_email_message(update, _make_context())
        text = update.message.reply_text.call_args[0][0]
        assert "non trovata" in text

    async def test_regular_user_becomes_pending(self):
        update = _make_update(chat_id=12345, text="regular@example.com")
        context = _make_context()
        await handle_email_message(update, context)

        await self.regular_user.arefresh_from_db()
        assert self.regular_user.telegram_status == User.TELEGRAM_STATUS_PENDING
        assert self.regular_user.telegram_chat_id == 12345

        text = update.message.reply_text.call_args[0][0]
        assert "attesa" in text

    async def test_regular_user_notifies_admins(self):
        update = _make_update(chat_id=12345, text="regular@example.com")
        context = _make_context()
        await handle_email_message(update, context)

        context.bot.send_message.assert_awaited_once()
        call_kwargs = context.bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == 55555

    async def test_staff_user_becomes_approved(self):
        await TelegramAuthSession.objects.acreate(
            chat_id=77777, phone_number="+39999000111"
        )
        update = _make_update(chat_id=77777, text="staff@example.com")
        await handle_email_message(update, _make_context())

        await self.staff_user.arefresh_from_db()
        assert self.staff_user.telegram_status == User.TELEGRAM_STATUS_APPROVED
        assert self.staff_user.telegram_chat_id == 77777

        text = update.message.reply_text.call_args[0][0]
        assert "admin" in text.lower()

    async def test_already_approved_user_gets_info(self):
        self.regular_user.telegram_chat_id = 12345
        self.regular_user.telegram_status = User.TELEGRAM_STATUS_APPROVED
        await self.regular_user.asave()

        update = _make_update(chat_id=12345, text="regular@example.com")
        await handle_email_message(update, _make_context())
        text = update.message.reply_text.call_args[0][0]
        assert "già collegato" in text

    async def test_already_pending_user_gets_info(self):
        self.regular_user.telegram_chat_id = 12345
        self.regular_user.telegram_status = User.TELEGRAM_STATUS_PENDING
        await self.regular_user.asave()

        update = _make_update(chat_id=12345, text="regular@example.com")
        await handle_email_message(update, _make_context())
        text = update.message.reply_text.call_args[0][0]
        assert "attesa" in text

    async def test_session_deleted_after_enrollment(self):
        update = _make_update(chat_id=12345, text="regular@example.com")
        await handle_email_message(update, _make_context())
        session_exists = await TelegramAuthSession.objects.filter(
            chat_id=12345
        ).aexists()
        assert not session_exists


@pytest.mark.django_db
class TestHandleEnrollmentApproval(TestCase):
    def setUp(self):
        self.pending_user = self.make_user("pending3@example.com")
        self.pending_user.telegram_chat_id = 44444
        self.pending_user.telegram_status = User.TELEGRAM_STATUS_PENDING
        self.pending_user.display_name = "Luigi"
        self.pending_user.save()

    async def test_approve_sets_status_approved(self):
        update = _make_callback_update(
            callback_data=f"approve_enrollment:{self.pending_user.id}"
        )
        context = _make_context()
        await handle_enrollment_approval(update, context)

        await self.pending_user.arefresh_from_db()
        assert self.pending_user.telegram_status == User.TELEGRAM_STATUS_APPROVED

        update.callback_query.edit_message_text.assert_awaited_once()
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Approvato" in text

    async def test_approve_notifies_user(self):
        update = _make_callback_update(
            callback_data=f"approve_enrollment:{self.pending_user.id}"
        )
        context = _make_context()
        await handle_enrollment_approval(update, context)

        context.bot.send_message.assert_awaited_once()
        call_kwargs = context.bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == 44444
        assert "approvata" in call_kwargs["text"].lower()

    async def test_reject_clears_user_telegram_data(self):
        update = _make_callback_update(
            callback_data=f"reject_enrollment:{self.pending_user.id}"
        )
        context = _make_context()
        await handle_enrollment_approval(update, context)

        await self.pending_user.arefresh_from_db()
        assert self.pending_user.telegram_chat_id is None
        assert self.pending_user.telegram_status is None

        update.callback_query.edit_message_text.assert_awaited_once()
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Rifiutato" in text

    async def test_reject_notifies_user(self):
        update = _make_callback_update(
            callback_data=f"reject_enrollment:{self.pending_user.id}"
        )
        context = _make_context()
        await handle_enrollment_approval(update, context)

        context.bot.send_message.assert_awaited_once()
        call_kwargs = context.bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == 44444
        assert "rifiutata" in call_kwargs["text"].lower()

    async def test_user_not_found_returns_error(self):
        update = _make_callback_update(callback_data="approve_enrollment:99999")
        await handle_enrollment_approval(update, _make_context())
        update.callback_query.edit_message_text.assert_awaited_once()
        text = update.callback_query.edit_message_text.call_args[0][0]
        assert "non trovato" in text
