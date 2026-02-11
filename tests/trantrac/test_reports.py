from decimal import Decimal
from unittest.mock import patch


from trantrac.reports import (
    aggregate_by_field,
    calculate_totals,
    fetch_sheet_transactions,
    filter_by_month,
    get_monthly_report_data,
    parse_italian_amount,
    parse_italian_date,
)


class TestParseItalianDate:
    def test_valid_date(self):
        result = parse_italian_date("15/01/2025")
        assert result is not None
        assert result.day == 15
        assert result.month == 1
        assert result.year == 2025

    def test_valid_date_with_spaces(self):
        result = parse_italian_date("  01/12/2024  ")
        assert result is not None
        assert result.day == 1
        assert result.month == 12
        assert result.year == 2024

    def test_iso_format(self):
        result = parse_italian_date("2025-01-15")
        assert result is not None
        assert result.day == 15
        assert result.month == 1
        assert result.year == 2025

    def test_iso_format_with_spaces(self):
        result = parse_italian_date("  2024-12-01  ")
        assert result is not None
        assert result.day == 1
        assert result.month == 12
        assert result.year == 2024

    def test_invalid_date_values(self):
        assert parse_italian_date("32/13/2025") is None

    def test_empty_string(self):
        assert parse_italian_date("") is None

    def test_none_like_value(self):
        assert parse_italian_date("not/a/date") is None

    def test_missing_parts(self):
        assert parse_italian_date("01/01") is None

    def test_two_digit_year(self):
        """ENTRATE sheet uses dd/mm/yy format"""
        result = parse_italian_date("01/01/26")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 1

    def test_two_digit_year_december(self):
        result = parse_italian_date("30/01/26")
        assert result is not None
        assert result.year == 2026

    def test_unknown_format(self):
        assert parse_italian_date("15-01-2025") is None


class TestParseItalianAmount:
    def test_simple_amount(self):
        assert parse_italian_amount("100,00") == Decimal("100.00")

    def test_amount_with_thousands(self):
        assert parse_italian_amount("1.234,56") == Decimal("1234.56")

    def test_amount_with_spaces(self):
        assert parse_italian_amount("  50,00  ") == Decimal("50.00")

    def test_integer_amount(self):
        assert parse_italian_amount("500") == Decimal("500")

    def test_invalid_amount(self):
        assert parse_italian_amount("invalid") == Decimal("0")

    def test_empty_string(self):
        assert parse_italian_amount("") == Decimal("0")

    def test_large_amount(self):
        assert parse_italian_amount("10.000,00") == Decimal("10000.00")

    def test_euro_symbol_prefix(self):
        """Google Sheets returns formatted amounts with € symbol"""
        assert parse_italian_amount("€ 1,54") == Decimal("1.54")

    def test_euro_symbol_no_space(self):
        assert parse_italian_amount("€1,54") == Decimal("1.54")

    def test_euro_symbol_with_thousands(self):
        assert parse_italian_amount("€ 1.234,56") == Decimal("1234.56")


class TestFilterByMonth:
    def _make_row(self, date_str, value="100,00"):
        return [date_str, value, "desc"]

    def test_filters_correct_month(self):
        rows = [
            ["Enrico", "15/01/2025", "100,00", "desc"],
            ["Enrico", "10/02/2025", "200,00", "desc"],
            ["Enrico", "20/01/2025", "300,00", "desc"],
        ]
        result = filter_by_month(rows, 2025, 1, date_col_idx=1)
        assert len(result) == 2
        assert result[0][2] == "100,00"
        assert result[1][2] == "300,00"

    def test_empty_rows(self):
        assert filter_by_month([], 2025, 1, date_col_idx=1) == []

    def test_no_matching_rows(self):
        rows = [["Enrico", "15/03/2025", "100,00", "desc"]]
        assert filter_by_month(rows, 2025, 1, date_col_idx=1) == []

    def test_skips_rows_with_invalid_dates(self):
        rows = [
            ["Enrico", "invalid-date", "100,00"],
            ["Enrico", "15/01/2025", "200,00"],
        ]
        result = filter_by_month(rows, 2025, 1, date_col_idx=1)
        assert len(result) == 1

    def test_skips_short_rows(self):
        rows = [["Enrico"]]
        assert filter_by_month(rows, 2025, 1, date_col_idx=1) == []

    def test_different_year(self):
        rows = [["Enrico", "15/01/2024", "100,00"]]
        assert filter_by_month(rows, 2025, 1, date_col_idx=1) == []

    def test_filters_iso_format_dates(self):
        """Dates saved by the web form use ISO format YYYY-MM-DD"""
        rows = [
            ["Enrico", "2025-01-15", "100,00", "desc"],
            ["Enrico", "2025-02-10", "200,00", "desc"],
            ["Viviana", "2025-01-20", "300,00", "desc"],
        ]
        result = filter_by_month(rows, 2025, 1, date_col_idx=1)
        assert len(result) == 2

    def test_mixed_date_formats(self):
        """Sheet may contain both ISO (web form) and Italian (CSV) dates"""
        rows = [
            ["Enrico", "2025-01-15", "100,00", "desc"],
            ["Viviana", "20/01/2025", "200,00", "desc"],
            ["Enrico", "10/02/2025", "300,00", "desc"],
        ]
        result = filter_by_month(rows, 2025, 1, date_col_idx=1)
        assert len(result) == 2


class TestAggregateByField:
    def test_aggregates_by_user(self):
        rows = [
            ["Enrico", "15/01/2025", "100,00"],
            ["Viviana", "16/01/2025", "200,00"],
            ["Enrico", "17/01/2025", "50,00"],
        ]
        result = aggregate_by_field(rows, field_idx=0, amount_idx=2)
        assert result["Enrico"] == Decimal("150.00")
        assert result["Viviana"] == Decimal("200.00")

    def test_empty_rows(self):
        assert aggregate_by_field([], field_idx=0, amount_idx=2) == {}

    def test_skips_short_rows(self):
        rows = [["Enrico"]]
        result = aggregate_by_field(rows, field_idx=0, amount_idx=2)
        assert result == {}

    def test_uses_sconosciuto_for_empty_field(self):
        rows = [["", "15/01/2025", "100,00"]]
        result = aggregate_by_field(rows, field_idx=0, amount_idx=2)
        assert "Sconosciuto" in result

    def test_aggregates_by_category(self):
        rows = [
            ["Enrico", "15/01/2025", "100,00", "desc", "Alimentari"],
            ["Viviana", "16/01/2025", "50,00", "desc", "Alimentari"],
            ["Enrico", "17/01/2025", "80,00", "desc", "Trasporti"],
        ]
        result = aggregate_by_field(rows, field_idx=4, amount_idx=2)
        assert result["Alimentari"] == Decimal("150.00")
        assert result["Trasporti"] == Decimal("80.00")


class TestCalculateTotals:
    def test_calculates_totals(self):
        income_rows = [
            ["Enrico", "15/01/2025", "1.000,00", "desc"],
            ["Viviana", "16/01/2025", "500,00", "desc"],
        ]
        expense_rows = [
            ["Enrico", "15/01/2025", "200,00", "desc", "Alimentari"],
            ["Viviana", "16/01/2025", "100,00", "desc", "Trasporti"],
        ]
        result = calculate_totals(income_rows, expense_rows)
        assert result["total_income"] == Decimal("1500.00")
        assert result["total_expenses"] == Decimal("300.00")
        assert result["balance"] == Decimal("1200.00")
        assert result["count_income"] == 2
        assert result["count_expenses"] == 2

    def test_empty_income(self):
        expense_rows = [["Enrico", "15/01/2025", "100,00", "desc"]]
        result = calculate_totals([], expense_rows)
        assert result["total_income"] == Decimal("0")
        assert result["total_expenses"] == Decimal("100.00")
        assert result["balance"] == Decimal("-100.00")

    def test_empty_expenses(self):
        income_rows = [["Enrico", "15/01/2025", "500,00", "desc"]]
        result = calculate_totals(income_rows, [])
        assert result["total_income"] == Decimal("500.00")
        assert result["total_expenses"] == Decimal("0")
        assert result["balance"] == Decimal("500.00")

    def test_both_empty(self):
        result = calculate_totals([], [])
        assert result["total_income"] == Decimal("0")
        assert result["total_expenses"] == Decimal("0")
        assert result["balance"] == Decimal("0")
        assert result["count_income"] == 0
        assert result["count_expenses"] == 0

    def test_skips_rows_with_missing_amount_col(self):
        income_rows = [["Enrico"]]  # missing amount column
        result = calculate_totals(income_rows, [])
        assert result["total_income"] == Decimal("0")


class TestFetchSheetTransactions:
    @patch("trantrac.reports.get_sheet_data")
    def test_fetches_entrate(self, mock_get):
        mock_get.return_value = [["Enrico", "15/01/2025", "100,00"]]
        result = fetch_sheet_transactions("ENTRATE")
        mock_get.assert_called_once_with("ENTRATE", "A2:Z")
        assert result == [["Enrico", "15/01/2025", "100,00"]]

    @patch("trantrac.reports.get_sheet_data")
    def test_returns_none_on_api_error(self, mock_get):
        mock_get.return_value = None
        result = fetch_sheet_transactions("ENTRATE")
        assert result is None


class TestGetMonthlyReportData:
    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_returns_none_when_no_transactions(self, mock_fetch):
        mock_fetch.return_value = []
        result = get_monthly_report_data(2025, 1)
        assert result is None

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_returns_data_when_transactions_exist(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [
                    ["Enrico", "15/01/2025", "1.000,00", "desc", "Stipendio", "ID1"]
                ]
            return [
                [
                    "Enrico",
                    "15/01/2025",
                    "200,00",
                    "desc",
                    "Alimentari",
                    "sub",
                    "Comune",
                    "ID2",
                ]
            ]

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        assert result is not None
        assert result["year"] == 2025
        assert result["month"] == 1
        assert result["total_income"] == Decimal("1000.00")
        assert result["total_expenses"] == Decimal("200.00")
        assert result["balance"] == Decimal("800.00")
        assert result["count_income"] == 1
        assert result["count_expenses"] == 1
        assert "Enrico" in result["income_by_user"]
        assert "Alimentari" in result["expenses_by_category"]
        assert (
            "Comune" in result["expenses_by_user"]
        )  # col 6 = "Comune" for CSV imports

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_filters_other_months(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [
                    ["Enrico", "15/01/2025", "500,00", "desc"],
                    ["Enrico", "15/02/2025", "300,00", "desc"],  # wrong month
                ]
            return []

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        assert result is not None
        assert result["total_income"] == Decimal("500.00")

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_returns_none_when_api_returns_none(self, mock_fetch):
        mock_fetch.return_value = None
        result = get_monthly_report_data(2025, 1)
        assert result is None

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_only_income_no_expenses(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [["Enrico", "15/01/2025", "500,00", "desc"]]
            return []

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        assert result is not None
        assert result["expenses_by_category"] == {}
        assert result["expenses_by_user"] == {}

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_only_expenses_no_income(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return []
            return [["Enrico", "15/01/2025", "200,00", "desc", "Alimentari"]]

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        assert result is not None
        assert result["income_by_user"] == {}

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_iso_dates_from_web_form(self, mock_fetch):
        """Expenses added via web form use YYYY-MM-DD dates; col 6 is the account owner"""

        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return []
            return [
                [
                    "Enrico",
                    "2025-01-10",
                    "150,00",
                    "desc",
                    "Alimentari",
                    "sub",
                    "Enrico",
                    "ID1",
                ],
                [
                    "Viviana",
                    "2025-01-20",
                    "80,00",
                    "desc",
                    "Trasporti",
                    "sub",
                    "Viviana",
                    "ID2",
                ],
            ]

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        assert result is not None
        assert result["total_expenses"] == Decimal("230.00")
        assert "Enrico" in result["expenses_by_user"]
        assert "Viviana" in result["expenses_by_user"]
        assert result["expenses_by_user"]["Enrico"] == Decimal("150.00")
        assert result["expenses_by_user"]["Viviana"] == Decimal("80.00")
