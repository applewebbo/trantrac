from datetime import date
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.core.management import call_command

from users.models import User


def make_approved_user(
    email="user@example.com", chat_id=123456, is_staff=False, is_superuser=False
):
    user = User.objects.create_user(email=email, password="password")
    user.telegram_chat_id = chat_id
    user.telegram_status = User.TELEGRAM_STATUS_APPROVED
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()
    return user


@pytest.mark.django_db
class TestSendTelegramReminderCommand:
    def test_no_approved_users(self):
        out = StringIO()
        call_command(
            "send_telegram_reminder", reminder_type="monthly", force=True, stdout=out
        )
        assert "No approved Telegram users found" in out.getvalue()

    def test_dry_run_monthly(self):
        make_approved_user()
        out = StringIO()
        call_command(
            "send_telegram_reminder",
            reminder_type="monthly",
            dry_run=True,
            force=True,
            stdout=out,
        )
        output = out.getvalue()
        assert "[dry-run]" in output
        assert "monthly" in output

    def test_dry_run_monthly_shows_user_and_admin_counts(self):
        make_approved_user(email="user@example.com", chat_id=100)
        make_approved_user(email="admin@example.com", chat_id=101, is_staff=True)
        out = StringIO()
        call_command(
            "send_telegram_reminder",
            reminder_type="monthly",
            dry_run=True,
            force=True,
            stdout=out,
        )
        output = out.getvalue()
        assert "1 user(s)" in output
        assert "1 admin(s)" in output

    def test_dry_run_weekly(self):
        make_approved_user()
        out = StringIO()
        call_command(
            "send_telegram_reminder",
            reminder_type="weekly",
            dry_run=True,
            stdout=out,
        )
        output = out.getvalue()
        assert "[dry-run]" in output
        assert "weekly" in output

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_sends_monthly_reminder(self, mock_bot_class):
        make_approved_user(chat_id=111)
        make_approved_user(email="other@example.com", chat_id=222)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        out = StringIO()
        call_command(
            "send_telegram_reminder", reminder_type="monthly", force=True, stdout=out
        )

        assert mock_bot.send_message.call_count == 2
        output = out.getvalue()
        assert "2 sent, 0 failed" in output

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_sends_weekly_reminder(self, mock_bot_class):
        make_approved_user(chat_id=333)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        out = StringIO()
        call_command("send_telegram_reminder", reminder_type="weekly", stdout=out)

        assert mock_bot.send_message.call_count == 1
        call_args = mock_bot.send_message.call_args
        assert "settimanale" in call_args.kwargs["text"]
        assert "1 sent, 0 failed" in out.getvalue()

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_monthly_user_message_content(self, mock_bot_class):
        make_approved_user(chat_id=444)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        call_command("send_telegram_reminder", reminder_type="monthly", force=True)

        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 444
        assert "mese scorso" in call_args.kwargs["text"]
        assert "3 giorni" in call_args.kwargs["text"]

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_monthly_admin_message_content(self, mock_bot_class):
        make_approved_user(chat_id=445, is_staff=True)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        call_command("send_telegram_reminder", reminder_type="monthly", force=True)

        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == 445
        assert "CSV" in call_args.kwargs["text"]
        assert "5 del mese" in call_args.kwargs["text"]

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_monthly_superuser_gets_admin_message(self, mock_bot_class):
        make_approved_user(chat_id=446, is_superuser=True)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        call_command("send_telegram_reminder", reminder_type="monthly", force=True)

        call_args = mock_bot.send_message.call_args
        assert "CSV" in call_args.kwargs["text"]

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_monthly_role_based_messages_sent(self, mock_bot_class):
        make_approved_user(email="user@example.com", chat_id=447)
        make_approved_user(email="admin@example.com", chat_id=448, is_staff=True)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        call_command("send_telegram_reminder", reminder_type="monthly", force=True)

        assert mock_bot.send_message.call_count == 2
        calls = {
            call.kwargs["chat_id"]: call.kwargs["text"]
            for call in mock_bot.send_message.call_args_list
        }
        assert "3 giorni" in calls[447]
        assert "CSV" in calls[448]

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_handles_send_failure(self, mock_bot_class):
        make_approved_user(chat_id=555)

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock(side_effect=Exception("Telegram error"))
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        out = StringIO()
        call_command("send_telegram_reminder", reminder_type="weekly", stdout=out)

        assert "0 sent, 1 failed" in out.getvalue()

    def test_monthly_skips_if_not_first_day(self):
        make_approved_user(chat_id=666)
        today = date.today()
        if today.day == 1:
            pytest.skip("Today is the 1st of the month")

        out = StringIO()
        call_command("send_telegram_reminder", reminder_type="monthly", stdout=out)
        assert "Skipping" in out.getvalue()

    @patch("telegram_bot.management.commands.send_telegram_reminder.Bot")
    def test_monthly_force_skips_date_check(self, mock_bot_class):
        make_approved_user(chat_id=777)
        today = date.today()
        if today.day == 1:
            pytest.skip("Today is already the 1st of the month")

        mock_bot = MagicMock()
        mock_bot.send_message = AsyncMock()
        mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
        mock_bot.__aexit__ = AsyncMock(return_value=False)
        mock_bot_class.return_value = mock_bot

        out = StringIO()
        call_command(
            "send_telegram_reminder", reminder_type="monthly", force=True, stdout=out
        )
        assert mock_bot.send_message.call_count == 1

    def test_weekly_no_date_check(self):
        """Weekly reminders are not subject to date checks."""
        out = StringIO()
        call_command("send_telegram_reminder", reminder_type="weekly", stdout=out)
        assert "Skipping" not in out.getvalue()
        assert "No approved Telegram users found" in out.getvalue()

    def test_skips_users_without_chat_id(self):
        user = User.objects.create_user(email="nochat@example.com", password="password")
        user.telegram_status = User.TELEGRAM_STATUS_APPROVED
        user.telegram_chat_id = None
        user.save()

        out = StringIO()
        call_command(
            "send_telegram_reminder", reminder_type="monthly", force=True, stdout=out
        )
        assert "No approved Telegram users found" in out.getvalue()
