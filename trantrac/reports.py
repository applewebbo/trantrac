import re
from decimal import Decimal, InvalidOperation

from trantrac.date_utils import parse_date as parse_italian_date
from trantrac.utils import get_sheet_data

# Column indices for ENTRATE sheet rows
ENTRATE_COL_USER = 0
ENTRATE_COL_DATE = 1
ENTRATE_COL_AMOUNT = 2
ENTRATE_COL_DESCRIPTION = 3

# Column indices for USCITE sheet rows
USCITE_COL_USER = 6
USCITE_COL_DATE = 1
USCITE_COL_AMOUNT = 2
USCITE_COL_DESCRIPTION = 3
USCITE_COL_CATEGORY = 4


def parse_italian_amount(amount_str: str) -> Decimal:
    """Parse Italian number format (1.234,56 or € 1,54) to Decimal"""
    try:
        normalized = (
            amount_str.strip().lstrip("€").strip().replace(".", "").replace(",", ".")
        )
        return Decimal(normalized)
    except InvalidOperation, AttributeError:
        return Decimal("0")


def filter_by_month(rows: list, year: int, month: int, date_col_idx: int) -> list:
    """Filter sheet rows to only those matching the given year and month"""
    result = []
    for row in rows:
        if len(row) <= date_col_idx:
            continue
        parsed = parse_italian_date(row[date_col_idx])
        if parsed and parsed.year == year and parsed.month == month:
            result.append(row)
    return result


def aggregate_by_field(
    rows: list, field_idx: int, amount_idx: int
) -> dict[str, Decimal]:
    """Aggregate amounts grouped by a field value"""
    totals: dict[str, Decimal] = {}
    for row in rows:
        if len(row) <= max(field_idx, amount_idx):
            continue
        key = row[field_idx].strip() if row[field_idx] else "Sconosciuto"
        amount = parse_italian_amount(row[amount_idx])
        totals[key] = totals.get(key, Decimal("0")) + amount
    return totals


def calculate_totals(income_rows: list, expense_rows: list) -> dict:
    """Calculate total income, expenses and balance from filtered rows"""
    total_income = sum(
        parse_italian_amount(row[ENTRATE_COL_AMOUNT])
        for row in income_rows
        if len(row) > ENTRATE_COL_AMOUNT
    )
    total_expenses = sum(
        parse_italian_amount(row[USCITE_COL_AMOUNT])
        for row in expense_rows
        if len(row) > USCITE_COL_AMOUNT
    )
    return {
        "total_income": Decimal(str(total_income)),
        "total_expenses": Decimal(str(total_expenses)),
        "balance": Decimal(str(total_income)) - Decimal(str(total_expenses)),
        "count_income": len(income_rows),
        "count_expenses": len(expense_rows),
    }


def fetch_sheet_transactions(sheet_name: str) -> list[list] | None:
    """Fetch all rows from the specified Google Sheets tab"""
    return get_sheet_data(sheet_name, "A2:Z")


def extract_da_label(description: str, trigger_string: str) -> str | None:
    """Find last whole-word occurrence of trigger_string; return stripped text after it, or None."""
    if not description or not trigger_string:
        return None
    word = re.escape(trigger_string.strip())
    matches = list(re.finditer(rf"\b{word}\b", description, re.IGNORECASE))
    if not matches:
        return None
    extracted = description[matches[-1].end() :].strip()
    return extracted or None


def is_standard_income(description: str, standard_keywords: list[str]) -> bool:
    """Return True if description contains any standard keyword (case-insensitive)."""
    if not standard_keywords:
        return False
    desc_upper = description.upper()
    return any(kw.upper() in desc_upper for kw in standard_keywords)


def build_income_by_user(
    income_rows: list,
    parsing_enabled: bool,
    trigger_string: str,
    standard_keywords: list[str],
) -> dict:
    """
    Build income dict grouped by user with standard/extra breakdown.

    Returns:
        {user: {"total": Decimal, "standard": [entries], "extra": [entries]}}
    where each entry is {"label": str, "amount": Decimal, "date": str}
    """
    result: dict = {}
    for row in income_rows:
        if len(row) <= ENTRATE_COL_AMOUNT:
            continue
        user = row[ENTRATE_COL_USER].strip() if row[ENTRATE_COL_USER] else "Sconosciuto"
        amount = parse_italian_amount(row[ENTRATE_COL_AMOUNT])
        date = row[ENTRATE_COL_DATE] if len(row) > ENTRATE_COL_DATE else ""
        description = (
            row[ENTRATE_COL_DESCRIPTION] if len(row) > ENTRATE_COL_DESCRIPTION else ""
        )

        label = description
        if parsing_enabled and trigger_string and description:
            extracted = extract_da_label(description, trigger_string)
            if extracted:
                label = extracted

        entry_type = (
            "standard"
            if is_standard_income(description, standard_keywords)
            else "extra"
        )

        if user not in result:
            result[user] = {"total": Decimal("0"), "standard": [], "extra": []}

        result[user]["total"] += amount
        result[user][entry_type].append(
            {"label": label, "amount": amount, "date": date}
        )

    return result


def build_expenses_by_category(expense_rows: list) -> dict:
    """
    Build expenses dict grouped by category with individual transactions.

    Returns:
        {category: {"total": Decimal, "transactions": [entries]}}
    where each entry is {"description": str, "amount": Decimal, "date": str}
    """
    result: dict = {}
    for row in expense_rows:
        if len(row) <= USCITE_COL_CATEGORY:
            continue
        category = (
            row[USCITE_COL_CATEGORY].strip()
            if row[USCITE_COL_CATEGORY]
            else "Sconosciuto"
        )
        amount = parse_italian_amount(row[USCITE_COL_AMOUNT])
        date = row[USCITE_COL_DATE] if len(row) > USCITE_COL_DATE else ""
        description = (
            row[USCITE_COL_DESCRIPTION] if len(row) > USCITE_COL_DESCRIPTION else ""
        )

        if category not in result:
            result[category] = {"total": Decimal("0"), "transactions": []}

        result[category]["total"] += amount
        result[category]["transactions"].append(
            {"description": description, "amount": amount, "date": date}
        )

    return result


def get_monthly_report_data(year: int, month: int) -> dict | None:
    """
    Fetch and aggregate transaction data for the given month.
    Returns None if there are no transactions for that month.
    """
    from trantrac.models import IncomeParsingConfig, StandardIncomeKeyword

    raw_income = fetch_sheet_transactions("ENTRATE") or []
    raw_expenses = fetch_sheet_transactions("USCITE") or []

    income_rows = filter_by_month(raw_income, year, month, ENTRATE_COL_DATE)
    expense_rows = filter_by_month(raw_expenses, year, month, USCITE_COL_DATE)

    if not income_rows and not expense_rows:
        return None

    config = IncomeParsingConfig.get_config()
    parsing_enabled = config.enabled if config else False
    trigger_string = config.trigger_string if config else "DA "
    standard_keywords = list(
        StandardIncomeKeyword.objects.values_list("keyword", flat=True)
    )

    totals = calculate_totals(income_rows, expense_rows)

    return {
        "year": year,
        "month": month,
        "income_by_user": build_income_by_user(
            income_rows, parsing_enabled, trigger_string, standard_keywords
        ),
        "expenses_by_category": build_expenses_by_category(expense_rows),
        "expenses_by_user": aggregate_by_field(
            expense_rows, USCITE_COL_USER, USCITE_COL_AMOUNT
        ),
        **totals,
    }
