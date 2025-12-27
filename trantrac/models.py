from django.conf import settings
from django.db import models
from google.oauth2 import service_account
from googleapiclient.discovery import build


def save_category_and_sub_to_sheet(values):
    credentials = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SHEETS_CREDENTIALS, scopes=settings.SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                range="CATEGORIE!A:B",
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


class Subcategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    skip_sheet_save = models.BooleanField(default=False)

    class Meta:
        verbose_name = "sottocategoria"
        verbose_name_plural = "sottocategorie"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.skip_sheet_save:
            values = [[self.category.name, self.name]]
            save_category_and_sub_to_sheet(values)
            pass
        super().save(*args, **kwargs)


class Account(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "conto bancario"
        verbose_name_plural = "conti bancari"


class CategoryUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "utilizzo categoria"
        verbose_name_plural = "utilizzi categorie"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["category", "subcategory"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.category} - {self.subcategory}"
