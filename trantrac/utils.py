import csv
from io import TextIOWrapper

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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


def save_to_sheet(values, sheet_name):
    """Save data to Google Sheets, appending to the first empty row"""
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
        return result.get("updates").get("updatedRows") == expected_rows
    finally:
        service.close()


def import_csv_to_sheet(csv_file, user):
    """Import CSV file to Google Sheets separating positive and negative transactions"""
    # Import here to avoid circular import
    from trantrac.models import (
        Category,
        Subcategory,
        UserMapping,
        save_category_and_sub_to_sheet,
    )

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

    if missing_columns := REQUIRED_COLUMNS - set(csv_reader.fieldnames):
        return (
            False,
            f"Il file CSV non contiene le seguenti colonne: {', '.join(missing_columns)}",
        )

    categories_subcategories = set()
    positive_values = []
    negative_values = []

    for row in csv_reader:
        if not any(row.values()) or any("Saldo" in value for value in row.values()):
            continue

        importo = row["Importo"].replace("+", "").strip()
        try:
            importo_float = float(importo.replace(".", "").replace(",", "."))
        except ValueError:
            return (
                False,
                "Il file CSV contiene valori non numerici nella colonna Importo.",
            )

        description = row["Descrizione"]
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
                str(row["Data operazione"]),
                importo,
                (description[:47] + "...") if len(description) > 50 else description,
                row["Categoria"],
                row["Codice identificativo"],
            ]
            positive_values.append(transaction_row)
        else:
            transaction_row = [
                str(user.display_name),
                str(row["Data operazione"]),
                importo.replace("-", ""),
                (description[:47] + "...") if len(description) > 50 else description,
                row["Categoria"],
                row["Sottocategoria"],
                "Comune",
                row["Codice identificativo"],
            ]
            negative_values.append(transaction_row)
            categories_subcategories.add((row["Categoria"], row["Sottocategoria"]))

    # Bulk create categories for negative transactions only
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

    # Handle subcategories for negative transactions only
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
        save_category_and_sub_to_sheet(subcategories_sheet_values)

    # Save transactions to respective sheets
    success_positive = save_to_sheet(positive_values, "ENTRATE")
    success_negative = save_to_sheet(negative_values, "USCITE")

    return (
        success_positive and success_negative,
        "File importato con successo"
        if (success_positive and success_negative)
        else "Ops, qualcosa è andato storto..",
    )


def get_sheet_data(sheet_name, range_name):
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
        return None
    finally:
        service.close()
