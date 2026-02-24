import logging
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def save_category_and_sub_to_sheet(values):
    """Save category and subcategory to Google Sheets"""
    from trantrac.utils import get_sheets_service

    sheets_settings = GoogleSheetsSettings.get_settings()
    service = get_sheets_service()

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
    except Exception:
        logger.exception("Failed to save categories to sheet")
        return False
    finally:
        service.close()


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorie"

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    skip_sheet_save = models.BooleanField(default=False)

    class Meta:
        verbose_name = "sottocategoria"
        verbose_name_plural = "sottocategorie"

    def __str__(self):
        return self.name


class Account(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "conto bancario"
        verbose_name_plural = "conti bancari"


class UserMapping(models.Model):
    """Maps CSV description keywords to user display names for positive transactions."""

    keyword = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Parola chiave",
        help_text="Keyword cercata nella descrizione della transazione (case insensitive)",
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name="Nome visualizzato",
        help_text="Nome utente da mostrare nel foglio",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Ordine",
        help_text="Priorità di corrispondenza (valore più basso = verificato prima)",
    )

    class Meta:
        verbose_name = "mappatura utente"
        verbose_name_plural = "mappature utenti"
        ordering = ["order", "keyword"]

    def __str__(self):
        return f"{self.keyword!r} → {self.display_name}"


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
            models.Index(fields=["user", "-created_at"]),
            # Covering index for filter(user, created_at__gte) + values("subcategory")
            models.Index(
                fields=["user", "-created_at", "subcategory"],
                name="idx_usage_user_date_sub",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.category} - {self.subcategory}"


@receiver(post_save, sender=Subcategory)
def sync_subcategory_to_sheets(sender, instance, created, **kwargs):
    """Sync newly created subcategories to Google Sheets."""
    if created and not getattr(instance, "skip_sheet_save", False):
        try:
            values = [[instance.category.name, instance.name]]
            save_category_and_sub_to_sheet(values)
        except Exception:
            logger.exception("Failed to sync subcategory '%s' to sheet", instance.name)


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

    CACHE_KEY = "google_sheets_settings"
    CACHE_TTL = 3600  # 1 hour

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance, cached for 1 hour."""
        cached = cache.get(cls.CACHE_KEY)
        if cached is not None:
            return cached
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
        cache.set(cls.CACHE_KEY, obj, cls.CACHE_TTL)
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


@receiver(post_save, sender=GoogleSheetsSettings)
def invalidate_sheets_settings_cache(sender, **kwargs):
    """Invalidate cached GoogleSheetsSettings when the model is saved."""
    cache.delete(GoogleSheetsSettings.CACHE_KEY)


def report_upload_path(instance, filename):
    """Generate UUID-based upload path for monthly reports"""
    return f"reports/{instance.year}/{uuid.uuid4()}.pdf"


class MonthlyReport(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    download_uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pdf_file = models.FileField(upload_to=report_upload_path, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    sheets_last_modified = models.DateTimeField(null=True, blank=True)
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_count_income = models.IntegerField(default=0)
    transaction_count_expenses = models.IntegerField(default=0)

    MONTH_NAMES = {
        1: "Gennaio",
        2: "Febbraio",
        3: "Marzo",
        4: "Aprile",
        5: "Maggio",
        6: "Giugno",
        7: "Luglio",
        8: "Agosto",
        9: "Settembre",
        10: "Ottobre",
        11: "Novembre",
        12: "Dicembre",
    }

    @property
    def month_name(self):
        return self.MONTH_NAMES.get(self.month, str(self.month))

    class Meta:
        verbose_name = "report mensile"
        verbose_name_plural = "report mensili"
        constraints = [
            models.UniqueConstraint(fields=["year", "month"], name="unique_year_month")
        ]
