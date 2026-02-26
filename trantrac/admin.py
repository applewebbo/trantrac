from django.contrib import admin

from trantrac.models import (
    Account,
    Category,
    GoogleSheetsSettings,
    MerchantMapping,
    MonthlyReport,
    Subcategory,
    UserKeywordPreference,
    UserMapping,
)


@admin.register(GoogleSheetsSettings)
class GoogleSheetsSettingsAdmin(admin.ModelAdmin):
    """Admin interface for Google Sheets settings (singleton)"""

    list_display = ("spreadsheet_id", "client_email", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        (
            "Spreadsheet",
            {
                "fields": ("spreadsheet_id",),
            },
        ),
        (
            "Service Account Credentials",
            {
                "fields": (
                    "project_id",
                    "client_email",
                    "client_id",
                    "private_key_id",
                    "private_key",
                    "client_x509_cert_url",
                ),
                "description": "Credenziali del service account Google per l'accesso alle API",
            },
        ),
        (
            "Info",
            {
                "fields": ("updated_at",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Prevent adding multiple instances (singleton)"""
        return not GoogleSheetsSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of settings"""
        return False


admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Account)


@admin.register(UserMapping)
class UserMappingAdmin(admin.ModelAdmin):
    list_display = ("keyword", "display_name", "order")
    ordering = ("order", "keyword")


@admin.register(MonthlyReport)
class MonthlyReportAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "month",
        "generated_at",
        "total_income",
        "total_expenses",
        "balance",
    )
    list_filter = ("year", "month")
    readonly_fields = (
        "pdf_file",
        "generated_at",
        "sheets_last_modified",
        "total_income",
        "total_expenses",
        "balance",
        "transaction_count_income",
        "transaction_count_expenses",
    )
    ordering = ("-year", "-month")


@admin.register(MerchantMapping)
class MerchantMappingAdmin(admin.ModelAdmin):
    list_display = ("keyword", "category", "subcategory")
    list_filter = ("category",)
    search_fields = ("keyword",)
    ordering = ("keyword",)
    autocomplete_fields = ()


@admin.register(UserKeywordPreference)
class UserKeywordPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "keyword", "category", "subcategory", "count")
    list_filter = ("category", "user")
    search_fields = ("keyword", "user__email")
    ordering = ("-count", "keyword")
