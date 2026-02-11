from datetime import date
from decimal import Decimal, InvalidOperation

from trantrac.utils import get_sheet_data


# Column indices for ENTRATE sheet rows
ENTRATE_COL_USER = 0
ENTRATE_COL_DATE = 1
ENTRATE_COL_AMOUNT = 2

# Column indices for USCITE sheet rows
USCITE_COL_USER = 6  # "Conto" column: Comune / Viviana / Enrico
USCITE_COL_DATE = 1
USCITE_COL_AMOUNT = 2
USCITE_COL_CATEGORY = 4


def parse_italian_date(date_str: str) -> date | None:
    """Parse date string in dd/mm/yyyy, dd/mm/yy or YYYY-MM-DD format to date object"""
    try:
        s = date_str.strip()
        if "-" in s and len(s) >= 8 and s[4] == "-":
            # ISO format: YYYY-MM-DD
            year, month, day = int(s[0:4]), int(s[5:7]), int(s[8:10])
        else:
            # Italian format: dd/mm/yyyy or dd/mm/yy
            parts = s.split("/")
            if len(parts) != 3:
                return None
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
        return date(year, month, day)
    except ValueError, AttributeError, IndexError:
        return None


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


def get_monthly_report_data(year: int, month: int) -> dict | None:
    """
    Fetch and aggregate transaction data for the given month.
    Returns None if there are no transactions for that month.
    """
    raw_income = fetch_sheet_transactions("ENTRATE") or []
    raw_expenses = fetch_sheet_transactions("USCITE") or []

    income_rows = filter_by_month(raw_income, year, month, ENTRATE_COL_DATE)
    expense_rows = filter_by_month(raw_expenses, year, month, USCITE_COL_DATE)

    if not income_rows and not expense_rows:
        return None

    totals = calculate_totals(income_rows, expense_rows)

    return {
        "year": year,
        "month": month,
        "income_by_user": aggregate_by_field(
            income_rows, ENTRATE_COL_USER, ENTRATE_COL_AMOUNT
        ),
        "expenses_by_category": aggregate_by_field(
            expense_rows, USCITE_COL_CATEGORY, USCITE_COL_AMOUNT
        ),
        "expenses_by_user": aggregate_by_field(
            expense_rows, USCITE_COL_USER, USCITE_COL_AMOUNT
        ),
        **totals,
    }
