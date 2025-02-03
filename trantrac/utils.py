import csv
from functools import lru_cache
from io import TextIOWrapper

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

from trantrac.models import Category, Subcategory, save_category_and_sub_to_sheet


@lru_cache(maxsize=1)
def get_sheets_service():
    """ " Get a service object for interacting with the Sheets API"""
    credentials = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SHEETS_CREDENTIALS, scopes=settings.SCOPES
    )
    return build("sheets", "v4", credentials=credentials)


def save_to_sheet(values):
    """Save data to Google Sheets"""
    service = get_sheets_service()

    body = {"values": values}
    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
            range="TRANSAZIONI!A:C",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )

    expected_rows = len(values)
    return result.get("updates").get("updatedRows") == expected_rows


def import_csv_to_sheet(csv_file, user):
    """Import CSV file to Google Sheets"""
    # Required columns for the CSV
    REQUIRED_COLUMNS = {
        "Data operazione",
        "Importo",
        "Descrizione",
        "Categoria",
        "Sottocategoria",
        "Codice identificativo",
    }

    # Convert the uploaded file to text mode
    file = TextIOWrapper(csv_file.file, encoding="utf-8")
    csv_reader = csv.DictReader(file)

    # Validate columns
    if missing_columns := REQUIRED_COLUMNS - set(csv_reader.fieldnames):
        return (
            False,
            f"Il file CSV non contiene le seguenti colonne: {', '.join(missing_columns)}",
        )

    # Process all rows in one pass
    categories_subcategories = set()
    values = []

    for row in csv_reader:
        # Skip empty rows and saldo rows
        if not any(row.values()) or any("Saldo" in value for value in row.values()):
            continue

        # Clean and validate importo
        importo = row["Importo"].replace("+", "").strip()
        try:
            # Convert European format (1.234,56) to float
            importo_float = float(importo.replace(".", "").replace(",", "."))
            if importo_float < 0:
                categories_subcategories.add((row["Categoria"], row["Sottocategoria"]))
        except ValueError:
            return (
                False,
                "Il file CSV contiene valori non numerici nella colonna Importo.",
            )

        # Prepare row for Google Sheet
        values.append(
            [
                str(user.display_name),
                row["Data operazione"],
                importo,
                (
                    (row["Descrizione"][:37] + "...")
                    if len(row["Descrizione"]) > 50
                    else row["Descrizione"]
                ),
                row["Categoria"],
                row["Sottocategoria"],
                "Comune",
                row["Codice identificativo"],
            ]
        )

    # Bulk create categories
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

    # Handle subcategories and their sheet saving
    existing_subcategories = {
        (sub.name, sub.category.name): sub
        for sub in Subcategory.objects.filter(
            category__in=existing_categories.values()
        ).select_related("category")
    }

    # Prepare subcategories data for Google Sheet
    subcategories_sheet_values = []

    for cat_name, subcat_name in categories_subcategories:
        if not subcat_name:
            continue

        if (subcat_name, cat_name) not in existing_subcategories:
            # Create new subcategory
            subcategory = Subcategory(
                name=subcat_name,
                category=existing_categories[cat_name],
                skip_sheet_save=True,  # Skip individual save method
            )
            subcategory.save()
            # Add to sheet values
            subcategories_sheet_values.append([cat_name, subcat_name])

    # Batch save new subcategories to sheet
    if subcategories_sheet_values:
        save_category_and_sub_to_sheet(subcategories_sheet_values)

    # Save transactions to Google Sheet
    success = save_to_sheet(values)
    return (
        success,
        "File importato con successo" if success else "Ops, qualcosa è andato storto..",
    )


def get_sheet_data(sheet_name, range_name):
    """Get data from specified sheet and range"""
    service = get_sheets_service()
    sheet = service.spreadsheets()

    try:
        result = (
            sheet.values()
            .get(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                range=f"{sheet_name}!{range_name}",
            )
            .execute()
        )

        return result.get("values", [])
    except Exception:
        return None
