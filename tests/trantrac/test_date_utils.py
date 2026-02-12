from datetime import date

from trantrac.date_utils import parse_date


class TestParseDate:
    def test_italian_format(self):
        result = parse_date("15/01/2025")
        assert result == date(2025, 1, 15)

    def test_italian_format_with_spaces(self):
        result = parse_date("  01/12/2024  ")
        assert result == date(2024, 12, 1)

    def test_two_digit_year(self):
        result = parse_date("01/01/26")
        assert result == date(2026, 1, 1)

    def test_two_digit_year_adds_2000(self):
        result = parse_date("31/12/99")
        assert result == date(2099, 12, 31)

    def test_iso_format(self):
        result = parse_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_iso_format_with_spaces(self):
        result = parse_date("  2024-12-01  ")
        assert result == date(2024, 12, 1)

    def test_invalid_date_values(self):
        assert parse_date("32/13/2025") is None

    def test_empty_string(self):
        assert parse_date("") is None

    def test_missing_parts(self):
        assert parse_date("01/01") is None

    def test_non_date_string(self):
        assert parse_date("not/a/date") is None

    def test_unknown_format(self):
        assert parse_date("15-01-2025") is None
