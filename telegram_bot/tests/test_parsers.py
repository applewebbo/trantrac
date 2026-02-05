"""Unit tests for transaction message parsing"""

from decimal import Decimal


from telegram_bot.services.parser import parse_transaction_message


def test_parse_valid_transaction():
    """Test parsing a valid transaction"""
    result = parse_transaction_message("50/caffè al bar")
    assert result is not None
    assert result["amount"] == Decimal("50.00")
    assert result["description"] == "caffè al bar"


def test_parse_decimal_with_dot():
    """Test parsing amount with decimal point"""
    result = parse_transaction_message("125.50/spesa settimanale")
    assert result is not None
    assert result["amount"] == Decimal("125.50")
    assert result["description"] == "spesa settimanale"


def test_parse_decimal_with_comma():
    """Test parsing amount with decimal comma (Italian format)"""
    result = parse_transaction_message("15,99/libro programmazione")
    assert result is not None
    assert result["amount"] == Decimal("15.99")
    assert result["description"] == "libro programmazione"


def test_parse_with_currency_symbol_euro():
    """Test parsing amount with € symbol"""
    result = parse_transaction_message("30€/pizza")
    assert result is not None
    assert result["amount"] == Decimal("30.00")
    assert result["description"] == "pizza"


def test_parse_with_currency_symbol_dollar():
    """Test parsing amount with $ symbol"""
    result = parse_transaction_message("$25/book")
    assert result is not None
    assert result["amount"] == Decimal("25.00")
    assert result["description"] == "book"


def test_parse_with_slash_in_description():
    """Test parsing when description contains slash"""
    result = parse_transaction_message("50/caffè/bar")
    assert result is not None
    assert result["amount"] == Decimal("50.00")
    assert result["description"] == "caffè/bar"


def test_parse_with_whitespace():
    """Test parsing with extra whitespace"""
    result = parse_transaction_message("  50  / caffè  ")
    assert result is not None
    assert result["amount"] == Decimal("50.00")
    assert result["description"] == "caffè"


def test_parse_invalid_no_separator():
    """Test parsing fails without separator"""
    result = parse_transaction_message("50 caffè")
    assert result is None


def test_parse_invalid_no_description():
    """Test parsing fails without description"""
    result = parse_transaction_message("50/")
    assert result is None


def test_parse_invalid_empty_description():
    """Test parsing fails with empty description after strip"""
    result = parse_transaction_message("50/   ")
    assert result is None


def test_parse_invalid_amount():
    """Test parsing fails with invalid amount"""
    result = parse_transaction_message("abc/caffè")
    assert result is None


def test_parse_negative_amount():
    """Test parsing fails with negative amount"""
    result = parse_transaction_message("-10/test")
    assert result is None


def test_parse_zero_amount():
    """Test parsing fails with zero amount"""
    result = parse_transaction_message("0/test")
    assert result is None


def test_parse_description_too_long():
    """Test parsing fails with description >200 characters"""
    long_desc = "x" * 201
    result = parse_transaction_message(f"50/{long_desc}")
    assert result is None


def test_parse_description_max_length():
    """Test parsing succeeds with description = 200 characters"""
    max_desc = "x" * 200
    result = parse_transaction_message(f"50/{max_desc}")
    assert result is not None
    assert result["description"] == max_desc


def test_parse_empty_message():
    """Test parsing fails with empty message"""
    result = parse_transaction_message("")
    assert result is None


def test_parse_none_message():
    """Test parsing fails with None message"""
    result = parse_transaction_message(None)
    assert result is None


def test_parse_decimal_precision():
    """Test parsing preserves decimal precision (2 decimal places)"""
    result = parse_transaction_message("10.50/test")
    assert result is not None
    assert result["amount"] == Decimal("10.50")
    # Verify 2 decimal places
    assert result["amount"].as_tuple().exponent == -2
