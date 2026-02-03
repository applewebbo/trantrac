from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from users.models import User


@pytest.mark.django_db
class TestSendMonthlyReminderCommand:
    def test_command_no_admin_users(self):
        """Test command when no admin users exist"""
        out = StringIO()
        call_command("send_monthly_reminder", stdout=out)

        output = out.getvalue()
        assert "No admin users found" in output

    @patch("trantrac.management.commands.send_monthly_reminder.send_mail")
    def test_command_sends_email_to_admin_users(self, mock_send_mail):
        """Test command sends email to admin users"""
        # Create admin users
        User.objects.create_superuser(email="admin@example.com", password="password")
        User.objects.create_user(
            email="staff@example.com", password="password", is_staff=True
        )

        out = StringIO()
        call_command("send_monthly_reminder", stdout=out)

        # Should have called send_mail twice (once for each admin)
        assert mock_send_mail.call_count == 2
        output = out.getvalue()
        assert "2 emails sent, 0 failed" in output

    @patch("trantrac.management.commands.send_monthly_reminder.send_mail")
    def test_command_with_site_url(self, mock_send_mail):
        """Test command includes upload URL when SITE_URL is set"""
        User.objects.create_superuser(email="admin@example.com", password="password")

        with patch("os.getenv", return_value="https://example.com"):
            out = StringIO()
            call_command("send_monthly_reminder", stdout=out)

        # Check email was sent with correct message
        assert mock_send_mail.called
        call_args = mock_send_mail.call_args
        message = call_args.kwargs["message"]
        assert "https://example.com" in message

    @patch("trantrac.management.commands.send_monthly_reminder.send_mail")
    def test_command_without_site_url(self, mock_send_mail):
        """Test command message when SITE_URL is not set"""
        User.objects.create_superuser(email="admin@example.com", password="password")

        with patch("os.getenv", return_value=""):
            out = StringIO()
            call_command("send_monthly_reminder", stdout=out)

        # Check email was sent with generic message
        assert mock_send_mail.called
        call_args = mock_send_mail.call_args
        message = call_args.kwargs["message"]
        assert "Accedi all'applicazione" in message

    @patch("trantrac.management.commands.send_monthly_reminder.send_mail")
    def test_command_handles_send_mail_failure(self, mock_send_mail):
        """Test command handles send_mail exceptions"""
        User.objects.create_superuser(email="admin@example.com", password="password")

        # Make send_mail raise an exception
        mock_send_mail.side_effect = Exception("Email service unavailable")

        out = StringIO()
        call_command("send_monthly_reminder", stdout=out)

        output = out.getvalue()
        assert "Failed to send email" in output
        assert "0 emails sent, 1 failed" in output

    @patch("trantrac.management.commands.send_monthly_reminder.send_mail")
    def test_command_email_content(self, mock_send_mail):
        """Test command email has correct subject and from address"""
        admin = User.objects.create_superuser(
            email="admin@example.com", password="password"
        )

        call_command("send_monthly_reminder", stdout=StringIO())

        assert mock_send_mail.called
        call_args = mock_send_mail.call_args
        assert call_args.kwargs["subject"] == "Reminder: Import transazioni bancarie"
        assert admin.email in call_args.kwargs["recipient_list"]

    @patch("trantrac.management.commands.send_monthly_reminder.send_mail")
    def test_command_deduplicates_users(self, mock_send_mail):
        """Test command sends only one email to users who are both staff and superuser"""
        # Create user who is both staff and superuser
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="password",
        )
        admin.is_staff = True
        admin.save()

        out = StringIO()
        call_command("send_monthly_reminder", stdout=out)

        # Should only send one email
        assert mock_send_mail.call_count == 1
        output = out.getvalue()
        assert "1 emails sent, 0 failed" in output
