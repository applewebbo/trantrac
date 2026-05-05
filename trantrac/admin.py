from django.contrib import admin

from trantrac.models import (
    Account,
    Category,
    GoogleSheetsSettings,
    IncomeParsingConfig,
    MerchantMapping,
    MonthlyReport,
    StandardIncomeKeyword,
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


@admin.register(IncomeParsingConfig)
class IncomeParsingConfigAdmin(admin.ModelAdmin):
    list_display = ("enabled", "trigger_string")

    def has_add_permission(self, request):
        return not IncomeParsingConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StandardIncomeKeyword)
class StandardIncomeKeywordAdmin(admin.ModelAdmin):
    list_display = ("keyword", "description")
    search_fields = ("keyword",)
    ordering = ("keyword",)


@admin.register(UserKeywordPreference)
class UserKeywordPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "keyword", "category", "subcategory", "count")
    list_filter = ("category", "user")
    search_fields = ("keyword", "user__email")
    ordering = ("-count", "keyword")


# ── Admin app-list reorganization ──────────────────────────────────────────
# Move report-related models out of the generic "Trantrac" section and into
# a dedicated "Report" section, without requiring a custom AdminSite or
# proxy models.

_REPORT_MODELS = {"monthlyreport", "incomeparsingconfig", "standardincomekeyword"}

_original_get_app_list = admin.AdminSite.get_app_list


def _get_app_list_with_report_section(self, request, app_label=None):
    app_list = _original_get_app_list(self, request, app_label)

    report_models = []
    for app in app_list:
        remaining = []
        for model in app["models"]:
            if model["object_name"].lower() in _REPORT_MODELS:
                report_models.append(model)
            else:
                remaining.append(model)
        app["models"] = remaining

    app_list = [app for app in app_list if app["models"]]

    if report_models:
        app_list.append(
            {
                "name": "Report",
                "app_label": "report",
                "app_url": "",
                "has_module_perms": True,
                "models": sorted(report_models, key=lambda m: m["name"]),
            }
        )

    return app_list


admin.AdminSite.get_app_list = _get_app_list_with_report_section
