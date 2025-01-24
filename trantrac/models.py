from django.db import models
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
                range="CATEGORIE!A:A",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

        return result.get("updates").get("updatedRows") == 1
    finally:
        service.close()


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorie"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        values = [[self.name]]
        save_to_sheet(values)
        super().save(*args, **kwargs)


class Account(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "conto bancario"
        verbose_name_plural = "conti bancari"
