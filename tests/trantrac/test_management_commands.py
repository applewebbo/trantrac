from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import MagicMock, patch

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


# ──────────────────────────────────────────────────────────────────────────────
# generate_monthly_report command
# ──────────────────────────────────────────────────────────────────────────────

from trantrac.management.commands.generate_monthly_report import get_previous_month  # noqa: E402


class TestGetPreviousMonth:
    def test_january_returns_december_previous_year(self):
        assert get_previous_month(date(2025, 1, 15)) == (2024, 12)

    def test_other_month_returns_previous_month(self):
        assert get_previous_month(date(2025, 3, 1)) == (2025, 2)
        assert get_previous_month(date(2025, 12, 31)) == (2025, 11)


@pytest.mark.django_db
class TestGenerateMonthlyReportCommand:
    CMD = "generate_monthly_report"

    def _make_report(self, year=2025, month=1):
        from trantrac.models import MonthlyReport

        report = MonthlyReport.objects.create(
            year=year,
            month=month,
            total_income=Decimal("1000"),
            total_expenses=Decimal("300"),
            balance=Decimal("700"),
        )
        report.pdf_file.name = f"reports/{year}/fake.pdf"
        report.save()
        return report

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_generates_report_for_explicit_month(self, mock_gen):
        mock_report = MagicMock()
        mock_report.total_income = Decimal("500")
        mock_report.total_expenses = Decimal("200")
        mock_report.balance = Decimal("300")
        mock_gen.return_value = mock_report

        out = StringIO()
        call_command(self.CMD, "--year=2025", "--month=3", stdout=out)

        mock_gen.assert_called_once_with(2025, 3)
        assert "generated successfully" in out.getvalue()

    @patch("trantrac.pdf_generator.generate_monthly_report")
    @patch("trantrac.management.commands.generate_monthly_report.date")
    def test_defaults_to_previous_month(self, mock_date, mock_gen):
        mock_date.today.return_value = date(2025, 4, 1)
        mock_report = MagicMock()
        mock_report.total_income = Decimal("0")
        mock_report.total_expenses = Decimal("0")
        mock_report.balance = Decimal("0")
        mock_gen.return_value = mock_report

        out = StringIO()
        call_command(self.CMD, stdout=out)

        mock_gen.assert_called_once_with(2025, 3)

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_skips_when_no_transactions(self, mock_gen):
        mock_gen.return_value = None

        out = StringIO()
        call_command(self.CMD, "--year=2025", "--month=2", stdout=out)

        assert "No transactions" in out.getvalue()

    def test_skips_when_report_already_exists(self):
        from trantrac.models import MonthlyReport

        report = MonthlyReport.objects.create(year=2025, month=5)
        MonthlyReport.objects.filter(pk=report.pk).update(
            pdf_file="reports/2025/fake.pdf"
        )

        out = StringIO()
        call_command(self.CMD, "--year=2025", "--month=5", stdout=out)

        assert "already exists" in out.getvalue()

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_force_regenerates_existing_report(self, mock_gen):
        from trantrac.models import MonthlyReport

        report = MonthlyReport.objects.create(year=2025, month=6)
        MonthlyReport.objects.filter(pk=report.pk).update(
            pdf_file="reports/2025/fake.pdf"
        )

        mock_report = MagicMock()
        mock_report.total_income = Decimal("100")
        mock_report.total_expenses = Decimal("50")
        mock_report.balance = Decimal("50")
        mock_gen.return_value = mock_report

        out = StringIO()
        call_command(self.CMD, "--year=2025", "--month=6", "--force", stdout=out)

        mock_gen.assert_called_once_with(2025, 6)
        assert "generated successfully" in out.getvalue()

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_dry_run_does_not_generate(self, mock_gen):
        out = StringIO()
        call_command(self.CMD, "--year=2025", "--month=7", "--dry-run", stdout=out)

        mock_gen.assert_not_called()
        assert "dry-run" in out.getvalue()

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_error_during_generation_exits_with_code_1(self, mock_gen):
        mock_gen.side_effect = Exception("Google Sheets unavailable")

        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command(self.CMD, "--year=2025", "--month=8", stderr=err)

        assert exc_info.value.code == 1
        assert "Error" in err.getvalue()

    def test_invalid_month_exits_with_code_1(self):
        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command(self.CMD, "--year=2025", "--month=13", stderr=err)

        assert exc_info.value.code == 1
        assert "Invalid month" in err.getvalue()

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_zero_month_exits_with_code_1(self, mock_gen):
        err = StringIO()
        with pytest.raises(SystemExit) as exc_info:
            call_command(self.CMD, "--year=2025", "--month=0", stderr=err)

        assert exc_info.value.code == 1
        mock_gen.assert_not_called()

    @patch("trantrac.pdf_generator.generate_monthly_report")
    @patch("trantrac.management.commands.generate_monthly_report.date")
    def test_january_auto_detects_december_previous_year(self, mock_date, mock_gen):
        """When run in January, should auto-generate for December of previous year"""
        mock_date.today.return_value = date(2026, 1, 1)
        mock_report = MagicMock()
        mock_report.total_income = Decimal("0")
        mock_report.total_expenses = Decimal("0")
        mock_report.balance = Decimal("0")
        mock_gen.return_value = mock_report

        call_command(self.CMD)

        mock_gen.assert_called_once_with(2025, 12)

    @patch("trantrac.pdf_generator.generate_monthly_report")
    def test_only_year_provided_uses_previous_month(self, mock_gen):
        """When only --year is given, month defaults to previous month of that year context"""
        mock_report = MagicMock()
        mock_report.total_income = Decimal("0")
        mock_report.total_expenses = Decimal("0")
        mock_report.balance = Decimal("0")
        mock_gen.return_value = mock_report

        # Only --month provided, year should auto-detect
        with patch(
            "trantrac.management.commands.generate_monthly_report.date"
        ) as mock_date:
            mock_date.today.return_value = date(2025, 6, 15)
            call_command(self.CMD, "--month=3")
            mock_gen.assert_called_once_with(2025, 3)
