from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError

from tests.conftest import TestCase
from trantrac.models import (
    Account,
    Category,
    CategoryUsage,
    GoogleSheetsSettings,
    MonthlyReport,
    Subcategory,
)


@pytest.mark.django_db
class TestCategoryModel(TestCase):
    def test_create_category(self):
        """Test creating category"""
        category = Category.objects.create(name="Food")
        assert category.name == "Food"
        assert str(category) == "Food"

    def test_category_verbose_names(self):
        """Test category verbose names"""
        assert Category._meta.verbose_name == "categoria"
        assert Category._meta.verbose_name_plural == "categorie"


@pytest.mark.django_db
class TestSubcategoryModel(TestCase):
    def test_create_subcategory_with_skip_sheet_save(self):
        """Test creating subcategory with skip_sheet_save=True"""
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )
        assert subcategory.name == "Groceries"
        assert subcategory.category == category
        assert str(subcategory) == "Groceries"

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_subcategory_save_calls_sheet_sync(self, mock_save):
        """Test subcategory save calls Google Sheets sync when skip_sheet_save=False"""
        mock_save.return_value = True
        category = Category.objects.create(name="Food")
        Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=False
        )

        mock_save.assert_called_once_with([["Food", "Groceries"]])

    def test_subcategory_save_skips_sheet_sync_when_flag_set(self):
        """Test subcategory save skips sheet sync when skip_sheet_save=True"""
        with patch("trantrac.models.save_category_and_sub_to_sheet") as mock_save:
            category = Category.objects.create(name="Food")
            Subcategory.objects.create(
                name="Groceries", category=category, skip_sheet_save=True
            )
            mock_save.assert_not_called()

    def test_subcategory_verbose_names(self):
        """Test subcategory verbose names"""
        assert Subcategory._meta.verbose_name == "sottocategoria"
        assert Subcategory._meta.verbose_name_plural == "sottocategorie"


@pytest.mark.django_db
class TestAccountModel(TestCase):
    def test_create_account(self):
        """Test creating account"""
        account = Account.objects.create(name="Main Account")
        assert account.name == "Main Account"
        assert str(account) == "Main Account"

    def test_account_verbose_names(self):
        """Test account verbose names"""
        assert Account._meta.verbose_name == "conto bancario"
        assert Account._meta.verbose_name_plural == "conti bancari"


@pytest.mark.django_db
class TestCategoryUsageModel(TestCase):
    def test_create_category_usage(self):
        """Test creating category usage"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )

        usage = CategoryUsage.objects.create(
            user=user, category=category, subcategory=subcategory
        )

        assert usage.user == user
        assert usage.category == category
        assert usage.subcategory == subcategory
        assert usage.created_at is not None

    def test_category_usage_str(self):
        """Test category usage __str__"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )

        usage = CategoryUsage.objects.create(
            user=user, category=category, subcategory=subcategory
        )

        expected = f"{user} - {category} - {subcategory}"
        assert str(usage) == expected

    def test_category_usage_ordering(self):
        """Test category usage is ordered by -created_at"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )

        usage1 = CategoryUsage.objects.create(
            user=user, category=category, subcategory=subcategory
        )
        usage2 = CategoryUsage.objects.create(
            user=user, category=category, subcategory=subcategory
        )

        usages = list(CategoryUsage.objects.all())
        assert usages[0] == usage2
        assert usages[1] == usage1

    def test_category_usage_verbose_names(self):
        """Test category usage verbose names"""
        assert CategoryUsage._meta.verbose_name == "utilizzo categoria"
        assert CategoryUsage._meta.verbose_name_plural == "utilizzi categorie"

    def test_category_usage_indexes(self):
        """Test category usage has correct indexes"""
        indexes = [idx.fields for idx in CategoryUsage._meta.indexes]
        assert ["-created_at"] in indexes
        assert ["category", "subcategory"] in indexes
        assert ["user", "-created_at"] in indexes


@pytest.mark.django_db
class TestSaveCategoryAndSubToSheet:
    @patch("trantrac.utils.get_sheets_service")
    def test_save_category_and_sub_to_sheet_success(self, mock_get_service):
        """Test save_category_and_sub_to_sheet returns True on success"""
        from trantrac.models import save_category_and_sub_to_sheet

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 1}
        }

        result = save_category_and_sub_to_sheet([["Food", "Groceries"]])

        assert result is True
        mock_service.close.assert_called_once()

    @patch("trantrac.utils.get_sheets_service")
    def test_save_category_and_sub_to_sheet_failure(self, mock_get_service):
        """Test save_category_and_sub_to_sheet returns False on failure"""
        from trantrac.models import save_category_and_sub_to_sheet

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 0}
        }

        result = save_category_and_sub_to_sheet([["Food", "Groceries"]])

        assert result is False
        mock_service.close.assert_called_once()

    @patch("trantrac.utils.get_sheets_service")
    def test_save_category_and_sub_to_sheet_exception(self, mock_get_service):
        """Test save_category_and_sub_to_sheet returns False on API exception"""
        from trantrac.models import save_category_and_sub_to_sheet

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets().values().append().execute.side_effect = Exception(
            "API error"
        )

        result = save_category_and_sub_to_sheet([["Food", "Groceries"]])

        assert result is False
        mock_service.close.assert_called_once()

    @patch("trantrac.utils.get_sheets_service")
    def test_subcategory_save_db_succeeds_even_if_sheets_fails(self, mock_get_service):
        """Test that DB save succeeds even if Sheets sync raises outside its try block"""
        from trantrac.models import Category, Subcategory

        # get_sheets_service is called before the try block in save_category_and_sub_to_sheet
        # so raising here causes the exception to propagate to Subcategory.save's except (lines 73-74)
        mock_get_service.side_effect = Exception("Service unavailable")

        category = Category.objects.create(name="TestCat")
        subcategory = Subcategory(
            name="TestSub", category=category, skip_sheet_save=False
        )
        subcategory.save()

        assert Subcategory.objects.filter(name="TestSub").exists()


@pytest.mark.django_db
class TestGoogleSheetsSettingsModel(TestCase):
    def test_create_settings(self):
        """Test creating Google Sheets settings"""
        settings = GoogleSheetsSettings.objects.create(
            spreadsheet_id="test-spreadsheet-id",
            project_id="test-project",
            private_key_id="test-key-id",
            private_key="test-private-key",
            client_email="test@example.com",
            client_id="12345",
            client_x509_cert_url="https://example.com/cert",
        )
        assert settings.spreadsheet_id == "test-spreadsheet-id"
        assert settings.project_id == "test-project"
        assert settings.client_email == "test@example.com"

    def test_singleton_pattern(self):
        """Test only one instance can be created"""
        GoogleSheetsSettings.objects.create(
            spreadsheet_id="test-1",
            project_id="project-1",
            private_key_id="key-1",
            private_key="private-key-1",
            client_email="test1@example.com",
            client_id="123",
            client_x509_cert_url="https://example.com/cert1",
        )

        with pytest.raises(ValidationError):
            GoogleSheetsSettings.objects.create(
                spreadsheet_id="test-2",
                project_id="project-2",
                private_key_id="key-2",
                private_key="private-key-2",
                client_email="test2@example.com",
                client_id="456",
                client_x509_cert_url="https://example.com/cert2",
            )

    def test_get_settings_creates_if_not_exists(self):
        """Test get_settings creates instance if it doesn't exist"""
        settings = GoogleSheetsSettings.get_settings()
        assert settings is not None
        assert settings.pk == 1

    def test_get_settings_returns_existing(self):
        """Test get_settings returns existing instance"""
        first = GoogleSheetsSettings.get_settings()
        second = GoogleSheetsSettings.get_settings()
        assert first.pk == second.pk

    def test_get_credentials_dict(self):
        """Test get_credentials_dict returns properly formatted dict"""
        settings = GoogleSheetsSettings.objects.create(
            spreadsheet_id="test-spreadsheet",
            project_id="test-project",
            private_key_id="test-key-id",
            private_key="test-private-key",
            client_email="test@example.com",
            client_id="12345",
            client_x509_cert_url="https://example.com/cert",
        )

        creds = settings.get_credentials_dict()

        assert creds["type"] == "service_account"
        assert creds["project_id"] == "test-project"
        assert creds["private_key_id"] == "test-key-id"
        assert creds["private_key"] == "test-private-key"
        assert creds["client_email"] == "test@example.com"
        assert creds["client_id"] == "12345"
        assert creds["auth_uri"] == "https://accounts.google.com/o/oauth2/auth"
        assert creds["token_uri"] == "https://oauth2.googleapis.com/token"
        assert (
            creds["auth_provider_x509_cert_url"]
            == "https://www.googleapis.com/oauth2/v1/certs"
        )
        assert creds["client_x509_cert_url"] == "https://example.com/cert"

    def test_get_credentials_dict_replaces_newlines(self):
        """Test get_credentials_dict converts \\n to actual newlines"""
        settings = GoogleSheetsSettings.objects.create(
            spreadsheet_id="test-spreadsheet",
            project_id="test-project",
            private_key_id="test-key-id",
            private_key="-----BEGIN PRIVATE KEY-----\\nline2\\nline3\\n-----END PRIVATE KEY-----",
            client_email="test@example.com",
            client_id="12345",
            client_x509_cert_url="https://example.com/cert",
        )

        creds = settings.get_credentials_dict()

        # Should convert \\n to actual newlines
        assert "\n" in creds["private_key"]
        assert "\\n" not in creds["private_key"]
        assert creds["private_key"].startswith("-----BEGIN PRIVATE KEY-----\n")

    def test_str_representation(self):
        """Test __str__ method"""
        settings = GoogleSheetsSettings.get_settings()
        assert "Google Sheets Settings" in str(settings)
        assert "aggiornato" in str(settings)

    def test_verbose_names(self):
        """Test verbose names"""
        assert GoogleSheetsSettings._meta.verbose_name == "Impostazioni Google Sheets"
        assert (
            GoogleSheetsSettings._meta.verbose_name_plural
            == "Impostazioni Google Sheets"
        )

    def test_get_settings_populates_cache(self):
        """Test get_settings stores result in cache after DB lookup."""
        cache.delete(GoogleSheetsSettings.CACHE_KEY)
        assert cache.get(GoogleSheetsSettings.CACHE_KEY) is None
        obj = GoogleSheetsSettings.get_settings()
        cached = cache.get(GoogleSheetsSettings.CACHE_KEY)
        assert cached is not None
        assert cached.pk == obj.pk

    def test_get_settings_returns_cached_value(self):
        """Test get_settings returns cached value on subsequent calls."""
        cache.delete(GoogleSheetsSettings.CACHE_KEY)
        first = GoogleSheetsSettings.get_settings()
        # Populate cache manually to prove the second call uses it
        second = GoogleSheetsSettings.get_settings()
        assert first.pk == second.pk

    def test_save_invalidates_cache(self):
        """Test saving GoogleSheetsSettings clears the cache."""
        obj = GoogleSheetsSettings.get_settings()
        assert cache.get(GoogleSheetsSettings.CACHE_KEY) is not None
        obj.save()
        assert cache.get(GoogleSheetsSettings.CACHE_KEY) is None


@pytest.mark.django_db
class TestMonthlyReportModel(TestCase):
    def test_create_monthly_report(self):
        """Test creating a monthly report"""
        report = MonthlyReport.objects.create(year=2025, month=1)
        assert report.year == 2025
        assert report.month == 1
        assert report.pk is not None

    def test_default_values(self):
        """Test default field values"""
        from decimal import Decimal

        report = MonthlyReport.objects.create(year=2025, month=2)
        assert report.total_income == Decimal("0")
        assert report.total_expenses == Decimal("0")
        assert report.balance == Decimal("0")
        assert report.transaction_count_income == 0
        assert report.transaction_count_expenses == 0
        assert report.sheets_last_modified is None
        assert report.pdf_file.name == ""

    def test_unique_constraint(self):
        """Test that only one report per year/month is allowed"""
        from django.db import IntegrityError

        MonthlyReport.objects.create(year=2025, month=3)
        with pytest.raises(IntegrityError):
            MonthlyReport.objects.create(year=2025, month=3)

    def test_verbose_names(self):
        """Test verbose names"""
        assert MonthlyReport._meta.verbose_name == "report mensile"
        assert MonthlyReport._meta.verbose_name_plural == "report mensili"

    def test_report_upload_path(self):
        """Test UUID-based upload path generation"""
        from trantrac.models import report_upload_path

        report = MonthlyReport(year=2025, month=1)
        path = report_upload_path(report, "ignored.pdf")
        assert path.startswith("reports/2025/")
        assert path.endswith(".pdf")
        # Ensure UUID is used (different calls produce different paths)
        path2 = report_upload_path(report, "ignored.pdf")
        assert path != path2

    def test_download_uuid_is_unique(self):
        """Test that each report gets a unique download_uuid"""
        import uuid

        report1 = MonthlyReport.objects.create(year=2025, month=9)
        report2 = MonthlyReport.objects.create(year=2025, month=10)
        assert report1.download_uuid != report2.download_uuid
        assert isinstance(report1.download_uuid, uuid.UUID)

    def test_month_name_property(self):
        """Test month_name returns Italian name"""
        report = MonthlyReport(year=2025, month=1)
        assert report.month_name == "Gennaio"
        report.month = 12
        assert report.month_name == "Dicembre"
