import csv
import logging
from datetime import datetime
from io import TextIOWrapper

from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
MAX_CSV_SIZE = 2 * 1024 * 1024  # 2MB
MAX_TEXT_FIELD_LENGTH = 100  # Match Category/Subcategory model max_length
MAX_TRANSACTION_AMOUNT = 1_000_000


def sanitize_csv_value(value: str) -> str:
    """Strip one leading formula-injection char (=, +, @) from text values."""
    value = value.strip()
    if value and value[0] in ("=", "+", "@"):
        return value[1:]
    return value


def get_sheets_service():
    """Get a service object for interacting with the Sheets API"""
    # Import here to avoid circular import
    from trantrac.models import GoogleSheetsSettings

    sheets_settings = GoogleSheetsSettings.get_settings()
    credentials = service_account.Credentials.from_service_account_info(
        sheets_settings.get_credentials_dict(), scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials)


def get_spreadsheet_id():
    """Get the current spreadsheet ID from settings"""
    # Import here to avoid circular import
    from trantrac.models import GoogleSheetsSettings

    return GoogleSheetsSettings.get_settings().spreadsheet_id


def save_to_sheet(values: list, sheet_name: str) -> tuple[bool, str]:
    """Save data to Google Sheets, appending to the first empty row."""
    service = get_sheets_service()
    spreadsheet_id = get_spreadsheet_id()

    try:
        # Get the current length of data in the sheet
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:C",
            )
            .execute()
        )

        current_rows = len(result.get("values", [])) if result.get("values") else 0
        start_row = current_rows + 1

        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A{start_row}:C{start_row}",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

        expected_rows = len(values)
        saved = result.get("updates").get("updatedRows") == expected_rows
        return saved, ""
    except Exception:
        logger.exception("Failed to save data to sheet '%s'", sheet_name)
        return False, ""
    finally:
        service.close()


def _ensure_categories_in_db(categories_subcategories: set) -> None:
    """Bulk-create missing categories and subcategories, syncing new ones to sheets."""
    from trantrac.models import Category, Subcategory, save_category_and_sub_to_sheet

    existing_categories = {
        cat.name: cat
        for cat in Category.objects.filter(
            name__in=[cat_name for cat_name, _ in categories_subcategories]
        )
    }

    new_categories = []
    for cat_name, _ in categories_subcategories:
        if cat_name not in existing_categories:
            new_cat = Category(name=cat_name)
            new_categories.append(new_cat)
            existing_categories[cat_name] = new_cat

    Category.objects.bulk_create(new_categories)

    existing_subcategories = {
        (sub.name, sub.category.name): sub
        for sub in Subcategory.objects.filter(
            category__in=existing_categories.values()
        ).select_related("category")
    }

    subcategories_sheet_values = []
    for cat_name, subcat_name in categories_subcategories:
        if not subcat_name:
            continue
        if (subcat_name, cat_name) not in existing_subcategories:
            subcategory = Subcategory(
                name=subcat_name,
                category=existing_categories[cat_name],
                skip_sheet_save=True,
            )
            subcategory.save()
            subcategories_sheet_values.append([cat_name, subcat_name])

    if subcategories_sheet_values:
        try:
            save_category_and_sub_to_sheet(subcategories_sheet_values)
        except Exception:
            logger.exception("Failed to sync new categories/subcategories to sheet")


def import_csv_to_sheet(csv_file, user) -> tuple[bool, str]:
    """Import CSV file to Google Sheets separating positive and negative transactions"""
    # Import here to avoid circular import
    from trantrac.models import UserMapping

    REQUIRED_COLUMNS = {
        "Data operazione",
        "Importo",
        "Descrizione",
        "Categoria",
        "Sottocategoria",
        "Codice identificativo",
    }

    file = TextIOWrapper(csv_file.file, encoding="utf-8")
    csv_reader = csv.DictReader(file)

    if missing_columns := REQUIRED_COLUMNS - set(csv_reader.fieldnames or []):
        return (
            False,
            f"Il file CSV non contiene le seguenti colonne: {', '.join(missing_columns)}",
        )

    existing_ids = get_existing_transaction_ids()
    categories_subcategories = set()
    positive_values = []
    negative_values = []
    skipped_count = 0

    for row in csv_reader:
        if not any(row.values()) or any("Saldo" in value for value in row.values()):
            continue

        codice = row["Codice identificativo"].strip()
        if codice and codice in existing_ids:
            skipped_count += 1
            continue

        # Validate date format
        date_str = row["Data operazione"].strip()
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            return (
                False,
                f"Data non valida: '{date_str}'. Formato atteso: gg/mm/aaaa.",
            )

        # Validate and parse amount
        importo = row["Importo"].replace("+", "").strip()
        try:
            importo_float = float(importo.replace(".", "").replace(",", "."))
        except ValueError:
            return (
                False,
                "Il file CSV contiene valori non numerici nella colonna Importo.",
            )

        if abs(importo_float) > MAX_TRANSACTION_AMOUNT:
            return (
                False,
                f"Importo troppo grande: {importo}. Massimo consentito: {MAX_TRANSACTION_AMOUNT:,}€.",
            )

        # Sanitize text fields
        description = sanitize_csv_value(row["Descrizione"])
        categoria = sanitize_csv_value(row["Categoria"])[:MAX_TEXT_FIELD_LENGTH]
        sottocategoria = sanitize_csv_value(row["Sottocategoria"])[
            :MAX_TEXT_FIELD_LENGTH
        ]
        desc_display = (
            (description[:47] + "...") if len(description) > 50 else description
        )

        if importo_float >= 0:
            # Determine user name based on configurable keyword mappings
            description_upper = description.upper()
            display_name = "Altro"
            for mapping in UserMapping.objects.all():
                if mapping.keyword.upper() in description_upper:
                    display_name = mapping.display_name
                    break

            transaction_row = [
                display_name,
                date_str,
                importo,
                desc_display,
                categoria,
                codice,
            ]
            positive_values.append(transaction_row)
        else:
            transaction_row = [
                str(user.display_name),
                date_str,
                importo.replace("-", ""),
                desc_display,
                categoria,
                sottocategoria,
                "Comune",
                codice,
            ]
            negative_values.append(transaction_row)
            categories_subcategories.add((categoria, sottocategoria))

    _ensure_categories_in_db(categories_subcategories)

    # Save transactions to respective sheets
    ok_positive, _ = save_to_sheet(positive_values, "ENTRATE")
    ok_negative, _ = save_to_sheet(negative_values, "USCITE")

    imported_count = len(positive_values) + len(negative_values)
    if ok_positive and ok_negative:
        msg = f"Importate {imported_count} transazioni"
        if skipped_count:
            msg += f", {skipped_count} duplicate saltate"
        return (True, msg)
    return (False, "Ops, qualcosa è andato storto..")


def get_existing_transaction_ids() -> set[str]:
    """Fetch all Codice identificativo from ENTRATE (col F) and USCITE (col H)."""
    service = get_sheets_service()
    spreadsheet_id = get_spreadsheet_id()
    try:
        result = (
            service.spreadsheets()
            .values()
            .batchGet(
                spreadsheetId=spreadsheet_id,
                ranges=["ENTRATE!F:F", "USCITE!H:H"],
            )
            .execute()
        )
        ids: set[str] = set()
        for value_range in result.get("valueRanges", []):
            for row in value_range.get("values", []):
                if row and row[0]:
                    ids.add(row[0])
        return ids
    finally:
        service.close()


def get_sheet_data(sheet_name: str, range_name: str) -> list | None:
    """Get data from specified sheet and range"""
    service = get_sheets_service()
    spreadsheet_id = get_spreadsheet_id()
    sheet = service.spreadsheets()

    try:
        result = (
            sheet.values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!{range_name}",
            )
            .execute()
        )

        return result.get("values", [])
    except Exception:
        logger.exception(
            "Failed to get sheet data from '%s!%s'", sheet_name, range_name
        )
        return None
    finally:
        service.close()


def delete_row_by_identifier(
    sheet_name: str, identifier: str, identifier_column: int
) -> bool:
    """
    Delete a row in a sheet by matching a unique identifier in a specific column.

    Searches for identifier in identifier_column (0-based), then deletes the matching row.
    Returns True on success, raises an exception on failure or if not found.
    """
    service = get_sheets_service()
    spreadsheet_id = get_spreadsheet_id()

    try:
        # Fetch the identifier column to find the row index
        col_letter = chr(ord("A") + identifier_column)
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!{col_letter}:{col_letter}",
            )
            .execute()
        )

        rows = result.get("values", [])
        row_index = next(
            (i for i, row in enumerate(rows) if row and row[0] == identifier),
            None,
        )

        if row_index is None:
            raise ValueError(
                f"Identifier '{identifier}' not found in sheet '{sheet_name}'"
            )

        # Get sheet_id (gid) for the named sheet
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = next(
            s["properties"]["sheetId"]
            for s in meta["sheets"]
            if s["properties"]["title"] == sheet_name
        )

        # Delete the row via batchUpdate
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {
                        "deleteDimension": {
                            "range": {
                                "sheetId": sheet_id,
                                "dimension": "ROWS",
                                "startIndex": row_index,
                                "endIndex": row_index + 1,
                            }
                        }
                    }
                ]
            },
        ).execute()

        return True
    finally:
        service.close()
