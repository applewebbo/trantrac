import csv
from io import TextIOWrapper

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def save_to_sheet(values):
    credentials = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SHEETS_CREDENTIALS, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    try:
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
    finally:
        service.close()


def import_csv_to_sheet(csv_file, user):
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
    file_columns = set(csv_reader.fieldnames)
    missing_columns = REQUIRED_COLUMNS - file_columns
    if missing_columns:
        message = f"Il file CSV non contiene le seguenti colonne: {', '.join(missing_columns)}"
        return False, message

    # Convert to list and filter out empty rows and saldo row
    rows = list(csv_reader)
    rows = [
        row
        for row in rows
        if any(row.values()) and not any("Saldo" in value for value in row.values())
    ]

    # Validate 'Importo' values
    for index, row in enumerate(rows, start=1):
        importo = (
            row["Importo"].replace("+", "").replace(".", "").replace(",", "").strip()
        )
        try:
            float(importo)
        except ValueError:
            message = "Il file CSV contiene valori non numerici nella colonna Importo."
            return False, message

    values = [
        [
            str(user.display_name),
            row["Data operazione"],
            row["Importo"].replace("+", "").replace(".", ""),
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
        for row in rows
    ]

    # Save to Google Sheet
    success = save_to_sheet(values)

    if success:
        message = "File importato con successo"
    else:
        message = "Ops, qualcosa è andato storto.."

    return success, message
