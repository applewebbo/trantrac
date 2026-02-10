from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from trantrac.pdf_generator import (
    MONTH_NAMES,
    convert_html_to_pdf,
    generate_monthly_report,
    render_report_template,
    save_report_file,
)


class TestMonthNames:
    def test_all_months_defined(self):
        assert len(MONTH_NAMES) == 12
        assert MONTH_NAMES[1] == "Gennaio"
        assert MONTH_NAMES[12] == "Dicembre"


class TestRenderReportTemplate:
    def _make_context(self, **kwargs):
        base = {
            "year": 2025,
            "month": 1,
            "month_name": "Gennaio",
            "generated_at": "01/02/2025 08:00",
            "total_income": Decimal("1000.00"),
            "total_expenses": Decimal("300.00"),
            "balance": Decimal("700.00"),
            "income_by_user": {"Enrico": Decimal("1000.00")},
            "expenses_by_category": {
                "Alimentari": Decimal("200.00"),
                "Trasporti": Decimal("100.00"),
            },
            "expenses_by_user": {"Enrico": Decimal("300.00")},
            "count_income": 1,
            "count_expenses": 2,
        }
        base.update(kwargs)
        return base

    def test_renders_html_string(self):
        context = self._make_context()
        html = render_report_template(context)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contains_month_name(self):
        context = self._make_context()
        html = render_report_template(context)
        assert "Gennaio" in html
        assert "2025" in html

    def test_contains_income_user(self):
        context = self._make_context()
        html = render_report_template(context)
        assert "Enrico" in html

    def test_contains_expense_category(self):
        context = self._make_context()
        html = render_report_template(context)
        assert "Alimentari" in html
        assert "Trasporti" in html

    def test_empty_income_shows_no_entrate_message(self):
        context = self._make_context(income_by_user={}, total_income=Decimal("0"))
        html = render_report_template(context)
        assert "Nessuna entrata" in html

    def test_empty_expenses_shows_no_uscite_message(self):
        context = self._make_context(
            expenses_by_category={},
            expenses_by_user={},
            total_expenses=Decimal("0"),
        )
        html = render_report_template(context)
        assert "Nessuna uscita" in html


class TestConvertHtmlToPdf:
    @patch("trantrac.pdf_generator.HTML")
    def test_returns_pdf_bytes(self, mock_html_class):
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"%PDF-1.4"
        mock_html_class.return_value = mock_html_instance

        result = convert_html_to_pdf("<html><body>test</body></html>")

        mock_html_class.assert_called_once_with(string="<html><body>test</body></html>")
        mock_html_instance.write_pdf.assert_called_once()
        assert result == b"%PDF-1.4"


class TestSaveReportFile:
    def test_saves_file_and_returns_relative_path(self, tmp_path):
        with override_settings(MEDIA_ROOT=tmp_path):
            pdf_bytes = b"%PDF-1.4 fake content"
            relative_path = save_report_file(pdf_bytes, 2025, 1)

            assert relative_path.startswith("reports/2025/")
            assert relative_path.endswith(".pdf")

            full_path = tmp_path / relative_path
            assert full_path.exists()
            assert full_path.read_bytes() == pdf_bytes

    def test_creates_year_directory(self, tmp_path):
        with override_settings(MEDIA_ROOT=tmp_path):
            save_report_file(b"content", 2026, 3)
            year_dir = tmp_path / "reports" / "2026"
            assert year_dir.is_dir()

    def test_each_call_generates_unique_filename(self, tmp_path):
        with override_settings(MEDIA_ROOT=tmp_path):
            path1 = save_report_file(b"content1", 2025, 1)
            path2 = save_report_file(b"content2", 2025, 1)
            assert path1 != path2


@pytest.mark.django_db
class TestGenerateMonthlyReport:
    @patch("trantrac.pdf_generator.get_monthly_report_data")
    def test_returns_none_when_no_data(self, mock_data):
        mock_data.return_value = None
        result = generate_monthly_report(2025, 1)
        assert result is None

    @patch("trantrac.pdf_generator.convert_html_to_pdf")
    @patch("trantrac.pdf_generator.get_monthly_report_data")
    def test_creates_monthly_report(self, mock_data, mock_pdf, tmp_path):
        mock_data.return_value = {
            "year": 2025,
            "month": 1,
            "total_income": Decimal("1000.00"),
            "total_expenses": Decimal("300.00"),
            "balance": Decimal("700.00"),
            "income_by_user": {"Enrico": Decimal("1000.00")},
            "expenses_by_category": {"Alimentari": Decimal("300.00")},
            "expenses_by_user": {"Enrico": Decimal("300.00")},
            "count_income": 2,
            "count_expenses": 3,
        }
        mock_pdf.return_value = b"%PDF-1.4 fake"

        with override_settings(MEDIA_ROOT=tmp_path):
            report = generate_monthly_report(2025, 1)

        assert report is not None
        assert report.year == 2025
        assert report.month == 1
        assert report.total_income == Decimal("1000.00")
        assert report.total_expenses == Decimal("300.00")
        assert report.balance == Decimal("700.00")
        assert report.transaction_count_income == 2
        assert report.transaction_count_expenses == 3
        assert report.pdf_file.name.startswith("reports/2025/")

    @patch("trantrac.pdf_generator.convert_html_to_pdf")
    @patch("trantrac.pdf_generator.get_monthly_report_data")
    def test_updates_existing_report(self, mock_data, mock_pdf, tmp_path):
        from trantrac.models import MonthlyReport

        mock_data.return_value = {
            "year": 2025,
            "month": 2,
            "total_income": Decimal("500.00"),
            "total_expenses": Decimal("100.00"),
            "balance": Decimal("400.00"),
            "income_by_user": {},
            "expenses_by_category": {},
            "expenses_by_user": {},
            "count_income": 1,
            "count_expenses": 1,
        }
        mock_pdf.return_value = b"%PDF-1.4 fake"

        with override_settings(MEDIA_ROOT=tmp_path):
            report1 = generate_monthly_report(2025, 2)
            report2 = generate_monthly_report(2025, 2)

        assert MonthlyReport.objects.filter(year=2025, month=2).count() == 1
        assert report1.pk == report2.pk
