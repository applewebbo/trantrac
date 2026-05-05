from decimal import Decimal
from unittest.mock import patch

import pytest

from trantrac.reports import (
    aggregate_by_field,
    build_expenses_by_category,
    build_income_by_user,
    calculate_totals,
    extract_da_label,
    fetch_sheet_transactions,
    filter_by_month,
    get_monthly_report_data,
    is_standard_income,
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


class TestExtractDaLabel:
    def test_finds_trigger_at_start(self):
        assert (
            extract_da_label("DA APPLE RETAIL ITALIA S.R.L.", "DA ")
            == "APPLE RETAIL ITALIA S.R.L."
        )

    def test_finds_trigger_in_middle(self):
        assert extract_da_label("ACCREDITO DA MARIO BIANCHI", "DA ") == "MARIO BIANCHI"

    def test_returns_none_when_not_found(self):
        assert extract_da_label("VOCIRETRIB. GENNAIO", "DA ") is None

    def test_case_insensitive_search(self):
        assert extract_da_label("accredito da mario rossi", "DA ") == "mario rossi"

    def test_returns_none_for_empty_description(self):
        assert extract_da_label("", "DA ") is None

    def test_returns_none_when_nothing_after_trigger(self):
        assert extract_da_label("ACCREDITO DA", "DA ") is None

    def test_uses_last_occurrence_when_multiple_triggers(self):
        assert extract_da_label("DA 01-04-2026 A 30-04-2026 DA INPS", "DA ") == "INPS"

    def test_does_not_match_trigger_inside_word(self):
        assert extract_da_label("DA MARIO BIANCHI", "DA") == "MARIO BIANCHI"

    def test_custom_trigger_string(self):
        assert extract_da_label("TRASF. PER MARCO", "PER ") == "MARCO"


class TestIsStandardIncome:
    def test_matches_keyword_in_description(self):
        assert is_standard_income("VOCIRETRIB. GENNAIO 2025", ["VOCIRETRIB."]) is True

    def test_matches_keyword_case_insensitive(self):
        assert is_standard_income("vociretrib. gennaio", ["VOCIRETRIB."]) is True

    def test_no_match(self):
        assert (
            is_standard_income(
                "DA APPLE RETAIL ITALIA", ["VOCIRETRIB.", "SPESE COMUNI"]
            )
            is False
        )

    def test_empty_keywords(self):
        assert is_standard_income("VOCIRETRIB.", []) is False

    def test_matches_partial_keyword(self):
        assert is_standard_income("SPESE COMUNI FEBBRAIO", ["SPESE COMUNI"]) is True

    def test_multiple_keywords_first_matches(self):
        assert (
            is_standard_income("VOCIRETRIB.", ["VOCIRETRIB.", "SPESE COMUNI"]) is True
        )

    def test_multiple_keywords_second_matches(self):
        assert (
            is_standard_income("SPESE COMUNI", ["VOCIRETRIB.", "SPESE COMUNI"]) is True
        )


class TestBuildIncomeByUser:
    def _make_row(self, user, date, amount, description=""):
        return [user, date, amount, description, "cat", "id"]

    def test_groups_by_user(self):
        rows = [
            self._make_row("Enrico", "15/01/2025", "1.000,00", "VOCIRETRIB."),
            self._make_row("Viviana", "16/01/2025", "500,00", "VOCIRETRIB."),
            self._make_row("Enrico", "17/01/2025", "200,00", "DA MARIO ROSSI"),
        ]
        result = build_income_by_user(rows, False, "DA ", [])
        assert "Enrico" in result
        assert "Viviana" in result
        assert result["Enrico"]["total"] == Decimal("1200.00")
        assert result["Viviana"]["total"] == Decimal("500.00")

    def test_classifies_standard_vs_extra(self):
        rows = [
            self._make_row("Enrico", "15/01/2025", "3.000,00", "VOCIRETRIB. GENNAIO"),
            self._make_row("Enrico", "20/01/2025", "50,00", "DA APPLE RETAIL"),
        ]
        result = build_income_by_user(rows, False, "DA ", ["VOCIRETRIB."])
        assert len(result["Enrico"]["standard"]) == 1
        assert len(result["Enrico"]["extra"]) == 1
        assert result["Enrico"]["standard"][0]["label"] == "VOCIRETRIB. GENNAIO"
        assert result["Enrico"]["extra"][0]["label"] == "DA APPLE RETAIL"

    def test_da_parsing_when_enabled(self):
        rows = [
            self._make_row(
                "Enrico", "20/01/2025", "50,00", "ACCREDITO DA APPLE RETAIL ITALIA"
            )
        ]
        result = build_income_by_user(rows, True, "DA ", [])
        assert result["Enrico"]["extra"][0]["label"] == "APPLE RETAIL ITALIA"

    def test_da_parsing_when_disabled(self):
        rows = [
            self._make_row(
                "Enrico", "20/01/2025", "50,00", "ACCREDITO DA APPLE RETAIL ITALIA"
            )
        ]
        result = build_income_by_user(rows, False, "DA ", [])
        assert (
            result["Enrico"]["extra"][0]["label"] == "ACCREDITO DA APPLE RETAIL ITALIA"
        )

    def test_da_parsing_only_when_trigger_found(self):
        rows = [self._make_row("Enrico", "20/01/2025", "50,00", "VOCIRETRIB. GENNAIO")]
        result = build_income_by_user(rows, True, "DA ", [])
        assert result["Enrico"]["extra"][0]["label"] == "VOCIRETRIB. GENNAIO"

    def test_empty_rows_returns_empty_dict(self):
        assert build_income_by_user([], False, "DA ", []) == {}

    def test_skips_rows_too_short(self):
        rows = [["Enrico"]]
        assert build_income_by_user(rows, False, "DA ", []) == {}

    def test_entry_contains_date(self):
        rows = [self._make_row("Enrico", "15/01/2025", "100,00", "VOCIRETRIB.")]
        result = build_income_by_user(rows, False, "DA ", [])
        assert result["Enrico"]["extra"][0]["date"] == "15/01/2025"

    def test_all_extra_when_no_keywords(self):
        rows = [
            self._make_row("Enrico", "15/01/2025", "3.000,00", "VOCIRETRIB. GENNAIO"),
            self._make_row("Enrico", "20/01/2025", "50,00", "DA APPLE RETAIL"),
        ]
        result = build_income_by_user(rows, False, "DA ", [])
        assert len(result["Enrico"]["standard"]) == 0
        assert len(result["Enrico"]["extra"]) == 2


class TestBuildExpensesByCategory:
    def _make_row(self, user, date, amount, description, category):
        return [user, date, amount, description, category, "sub", "Comune", "id"]

    def test_groups_by_category(self):
        rows = [
            self._make_row(
                "Enrico", "15/01/2025", "50,00", "Caffè", "Bar e Ristoranti"
            ),
            self._make_row(
                "Viviana", "16/01/2025", "100,00", "Ristorante", "Bar e Ristoranti"
            ),
            self._make_row("Enrico", "17/01/2025", "80,00", "Esselunga", "Alimentari"),
        ]
        result = build_expenses_by_category(rows)
        assert "Bar e Ristoranti" in result
        assert "Alimentari" in result
        assert result["Bar e Ristoranti"]["total"] == Decimal("150.00")
        assert result["Alimentari"]["total"] == Decimal("80.00")

    def test_transactions_listed_under_category(self):
        rows = [
            self._make_row(
                "Enrico", "15/01/2025", "50,00", "Caffè", "Bar e Ristoranti"
            ),
            self._make_row(
                "Viviana", "16/01/2025", "100,00", "Ristorante", "Bar e Ristoranti"
            ),
        ]
        result = build_expenses_by_category(rows)
        txs = result["Bar e Ristoranti"]["transactions"]
        assert len(txs) == 2
        assert txs[0]["description"] == "Caffè"
        assert txs[0]["amount"] == Decimal("50.00")
        assert txs[0]["date"] == "15/01/2025"
        assert txs[1]["description"] == "Ristorante"

    def test_empty_rows_returns_empty_dict(self):
        assert build_expenses_by_category([]) == {}

    def test_skips_rows_too_short(self):
        rows = [["Enrico", "15/01/2025", "50,00"]]
        assert build_expenses_by_category(rows) == {}

    def test_fallback_category_name(self):
        rows = [["Enrico", "15/01/2025", "50,00", "desc", "", "sub", "Comune", "id"]]
        result = build_expenses_by_category(rows)
        assert "Sconosciuto" in result


@pytest.mark.django_db
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
                    [
                        "Enrico",
                        "15/01/2025",
                        "1.000,00",
                        "VOCIRETRIB.",
                        "Stipendio",
                        "ID1",
                    ]
                ]
            return [
                [
                    "Enrico",
                    "15/01/2025",
                    "200,00",
                    "Esselunga",
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
        assert "Comune" in result["expenses_by_user"]

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_income_by_user_has_structured_data(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [
                    ["Enrico", "15/01/2025", "1.000,00", "VOCIRETRIB.", "cat", "ID1"]
                ]
            return []

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        enrico = result["income_by_user"]["Enrico"]
        assert "total" in enrico
        assert "standard" in enrico
        assert "extra" in enrico
        assert enrico["total"] == Decimal("1000.00")

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_expenses_by_category_has_structured_data(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return []
            return [
                [
                    "Enrico",
                    "15/01/2025",
                    "50,00",
                    "Caffè",
                    "Bar e Ristoranti",
                    "sub",
                    "Comune",
                    "ID1",
                ]
            ]

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        bar = result["expenses_by_category"]["Bar e Ristoranti"]
        assert "total" in bar
        assert "transactions" in bar
        assert bar["total"] == Decimal("50.00")
        assert len(bar["transactions"]) == 1

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_filters_other_months(self, mock_fetch):
        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [
                    ["Enrico", "15/01/2025", "500,00", "desc"],
                    ["Enrico", "15/02/2025", "300,00", "desc"],
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
            return [
                [
                    "Enrico",
                    "15/01/2025",
                    "200,00",
                    "desc",
                    "Alimentari",
                    "sub",
                    "Comune",
                    "ID1",
                ]
            ]

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        assert result is not None
        assert result["income_by_user"] == {}

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_iso_dates_from_web_form(self, mock_fetch):
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

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_uses_income_parsing_config_from_db(self, mock_fetch):
        from trantrac.models import IncomeParsingConfig

        IncomeParsingConfig.objects.create(enabled=True, trigger_string="DA ")

        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [["Enrico", "15/01/2025", "50,00", "ACCREDITO DA APPLE RETAIL"]]
            return []

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        entry = result["income_by_user"]["Enrico"]["extra"][0]
        assert entry["label"] == "APPLE RETAIL"

    @patch("trantrac.reports.fetch_sheet_transactions")
    def test_uses_standard_keywords_from_db(self, mock_fetch):
        from trantrac.models import StandardIncomeKeyword

        StandardIncomeKeyword.objects.create(keyword="VOCIRETRIB.")

        def side_effect(sheet_name):
            if sheet_name == "ENTRATE":
                return [
                    ["Enrico", "15/01/2025", "3.000,00", "VOCIRETRIB. GENNAIO"],
                    ["Enrico", "20/01/2025", "50,00", "DA APPLE RETAIL"],
                ]
            return []

        mock_fetch.side_effect = side_effect
        result = get_monthly_report_data(2025, 1)
        enrico = result["income_by_user"]["Enrico"]
        assert len(enrico["standard"]) == 1
        assert len(enrico["extra"]) == 1
