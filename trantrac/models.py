from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from google.oauth2 import service_account
from googleapiclient.discovery import build


def save_category_and_sub_to_sheet(values):
    """Save category and subcategory to Google Sheets"""
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    # Get settings from database
    sheets_settings = GoogleSheetsSettings.get_settings()
    credentials = service_account.Credentials.from_service_account_info(
        sheets_settings.get_credentials_dict(), scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=sheets_settings.spreadsheet_id,
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


class GoogleSheetsSettings(models.Model):
    """Singleton model to store Google Sheets API configuration"""

    spreadsheet_id = models.CharField(
        max_length=200,
        verbose_name="Spreadsheet ID",
        help_text="ID del foglio Google Sheets (dalla URL)",
    )
    project_id = models.CharField(
        max_length=200,
        verbose_name="Project ID",
    )
    private_key_id = models.CharField(
        max_length=200,
        verbose_name="Private Key ID",
    )
    private_key = models.TextField(
        verbose_name="Private Key",
        help_text="Chiave privata del service account",
    )
    client_email = models.EmailField(
        verbose_name="Client Email",
        help_text="Email del service account",
    )
    client_id = models.CharField(
        max_length=200,
        verbose_name="Client ID",
    )
    client_x509_cert_url = models.URLField(
        max_length=500,
        verbose_name="Client x509 Cert URL",
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Ultimo aggiornamento"
    )

    class Meta:
        verbose_name = "Impostazioni Google Sheets"
        verbose_name_plural = "Impostazioni Google Sheets"

    def __str__(self):
        return f"Google Sheets Settings (aggiornato: {self.updated_at})"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)"""
        if not self.pk and GoogleSheetsSettings.objects.exists():
            msg = "Esiste già una configurazione Google Sheets. Modificala invece di crearne una nuova."
            raise ValidationError(msg)
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance"""
        obj, _created = cls.objects.get_or_create(
            pk=1,
            defaults={
                "spreadsheet_id": getattr(settings, "GOOGLE_SHEETS_SPREADSHEET_ID", ""),
                "project_id": settings.GOOGLE_SHEETS_CREDENTIALS.get("project_id", ""),
                "private_key_id": settings.GOOGLE_SHEETS_CREDENTIALS.get(
                    "private_key_id", ""
                ),
                "private_key": settings.GOOGLE_SHEETS_CREDENTIALS.get(
                    "private_key", ""
                ),
                "client_email": settings.GOOGLE_SHEETS_CREDENTIALS.get(
                    "client_email", ""
                ),
                "client_id": settings.GOOGLE_SHEETS_CREDENTIALS.get("client_id", ""),
                "client_x509_cert_url": settings.GOOGLE_SHEETS_CREDENTIALS.get(
                    "client_x509_cert_url", ""
                ),
            },
        )
        return obj

    def get_credentials_dict(self):
        """Return credentials in the format expected by Google API"""
        return {
            "type": "service_account",
            "project_id": self.project_id,
            "private_key_id": self.private_key_id,
            "private_key": self.private_key.replace("\\n", "\n"),
            "client_email": self.client_email,
            "client_id": self.client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",  # nosec B105
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": self.client_x509_cert_url,
        }
