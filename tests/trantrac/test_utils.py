from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile

from tests.conftest import TestCase
from trantrac.models import Category, Subcategory
from trantrac.utils import (
    get_sheet_data,
    get_sheets_service,
    import_csv_to_sheet,
    save_to_sheet,
)


@pytest.mark.django_db
class TestGetSheetsService:
    @patch("trantrac.utils.build")
    @patch("trantrac.utils.service_account.Credentials.from_service_account_info")
    def test_get_sheets_service_returns_service(self, mock_creds, mock_build):
        """Test get_sheets_service returns Google Sheets service"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Clear cache first
        get_sheets_service.cache_clear()

        service = get_sheets_service()

        assert service == mock_service
        mock_build.assert_called_once()

    @patch("trantrac.utils.build")
    @patch("trantrac.utils.service_account.Credentials.from_service_account_info")
    def test_get_sheets_service_cached(self, mock_creds, mock_build):
        """Test get_sheets_service uses cache"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Clear cache first
        get_sheets_service.cache_clear()

        # Call twice
        service1 = get_sheets_service()
        service2 = get_sheets_service()

        assert service1 == service2
        # Should only build once due to caching
        assert mock_build.call_count == 1


@pytest.mark.django_db
class TestSaveToSheet:
    @patch("trantrac.utils.get_sheets_service")
    def test_save_to_sheet_success(self, mock_get_service):
        """Test save_to_sheet returns True on success"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Mock get response (empty sheet)
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        # Mock append response
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 1}
        }

        values = [
            ["User", "2025-01-15", "100.50", "Test", "Food", "Groceries", "Account"]
        ]
        result = save_to_sheet(values, "USCITE")

        assert result is True

    @patch("trantrac.utils.get_sheets_service")
    def test_save_to_sheet_failure(self, mock_get_service):
        """Test save_to_sheet returns False on failure"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 0}
        }

        values = [
            ["User", "2025-01-15", "100.50", "Test", "Food", "Groceries", "Account"]
        ]
        result = save_to_sheet(values, "USCITE")

        assert result is False

    @patch("trantrac.utils.get_sheets_service")
    def test_save_to_sheet_appends_to_correct_row(self, mock_get_service):
        """Test save_to_sheet appends to correct row when sheet has data"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Mock sheet with 5 existing rows
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["row1"], ["row2"], ["row3"], ["row4"], ["row5"]]
        }

        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 1}
        }

        values = [["New", "Row"]]
        save_to_sheet(values, "USCITE")

        # Should append to row 6
        append_call = mock_service.spreadsheets().values().append
        assert "USCITE!A6:C6" in str(append_call.call_args)


@pytest.mark.django_db
class TestGetSheetData:
    @patch("trantrac.utils.get_sheets_service")
    def test_get_sheet_data_success(self, mock_get_service):
        """Test get_sheet_data returns data on success"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["Food", "Groceries"], ["Transport", "Bus"]]
        }

        result = get_sheet_data("CATEGORIE", "A2:B")

        assert result == [["Food", "Groceries"], ["Transport", "Bus"]]

    @patch("trantrac.utils.get_sheets_service")
    def test_get_sheet_data_empty(self, mock_get_service):
        """Test get_sheet_data returns empty list when no values"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {}

        result = get_sheet_data("CATEGORIE", "A2:B")

        assert result == []

    @patch("trantrac.utils.get_sheets_service")
    def test_get_sheet_data_exception(self, mock_get_service):
        """Test get_sheet_data returns None on exception"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.side_effect = Exception(
            "API Error"
        )

        result = get_sheet_data("CATEGORIE", "A2:B")

        assert result is None


@pytest.mark.django_db
class TestImportCsvToSheet(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")

    def create_csv_file(self, content):
        """Helper to create InMemoryUploadedFile from CSV content"""
        csv_bytes = content.encode("utf-8")
        csv_file = InMemoryUploadedFile(
            BytesIO(csv_bytes),
            field_name="csv_file",
            name="test.csv",
            content_type="text/csv",
            size=len(csv_bytes),
            charset="utf-8",
        )
        return csv_file

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_success(self, mock_save_cat, mock_save_sheet):
        """Test successful CSV import"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123
02/01/2025,+500.00,ENRICO Test Income,Salary,,DEF456"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        assert "File importato con successo" in message

    @patch("trantrac.utils.save_to_sheet")
    def test_import_csv_missing_columns(self, mock_save_sheet):
        """Test CSV import with missing columns"""
        csv_content = """Data operazione,Importo,Descrizione
01/01/2025,-100.50,Test Transaction"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is False
        assert "non contiene le seguenti colonne" in message

    @patch("trantrac.utils.save_to_sheet")
    def test_import_csv_invalid_amount(self, mock_save_sheet):
        """Test CSV import with invalid amount value"""
        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,invalid,Test Transaction,Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is False
        assert "valori non numerici" in message

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_creates_categories(self, mock_save_cat, mock_save_sheet):
        """Test CSV import creates new categories"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,NewCategory,NewSubcat,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        assert Category.objects.filter(name="NewCategory").exists()
        assert Subcategory.objects.filter(name="NewSubcat").exists()

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_skips_empty_subcategory(self, mock_save_cat, mock_save_sheet):
        """Test CSV import skips empty subcategory names"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        # Category should be created but no subcategory
        assert Category.objects.filter(name="Food").exists()
        # save_category_and_sub_to_sheet should not be called since subcategory is empty
        mock_save_cat.assert_not_called()

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_separates_positive_negative(
        self, mock_save_cat, mock_save_sheet
    ):
        """Test CSV import separates positive and negative transactions"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Expense,Food,Groceries,ABC123
02/01/2025,+500.00,ENRICO Income,Salary,,DEF456"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        # Check that save_to_sheet was called twice (ENTRATE and USCITE)
        assert mock_save_sheet.call_count == 2

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_user_name_detection(self, mock_save_cat, mock_save_sheet):
        """Test CSV import detects user names in positive transactions"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,+100.00,VIVIANA Income,Salary,,ABC123
02/01/2025,+200.00,ENRICO Income,Salary,,DEF456
03/01/2025,+300.00,APPLE Income,Salary,,GHI789
04/01/2025,+400.00,Other Income,Salary,,JKL012"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        # Get the ENTRATE call
        entrate_call = [
            call for call in mock_save_sheet.call_args_list if call[0][1] == "ENTRATE"
        ][0]
        values = entrate_call[0][0]

        # Check user names
        assert values[0][0] == "Viviana"
        assert values[1][0] == "Enrico"
        assert values[2][0] == "Enrico"
        assert values[3][0] == "Altro"

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_skips_saldo_rows(self, mock_save_cat, mock_save_sheet):
        """Test CSV import skips rows containing 'Saldo'"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123
02/01/2025,0.00,Saldo iniziale,,,
03/01/2025,+200.00,ENRICO Income,Salary,,DEF456"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        # Should have called save_to_sheet twice (once for ENTRATE, once for USCITE)
        # but Saldo row should be skipped
        assert mock_save_sheet.call_count == 2

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_truncates_long_descriptions(
        self, mock_save_cat, mock_save_sheet
    ):
        """Test CSV import truncates descriptions longer than 50 characters"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        long_desc = "A" * 60
        csv_content = f"""Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,{long_desc},Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        # Get the USCITE call
        uscite_call = [
            call for call in mock_save_sheet.call_args_list if call[0][1] == "USCITE"
        ][0]
        description = uscite_call[0][0][0][3]

        assert len(description) == 50
        assert description.endswith("...")

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_reuses_existing_categories(
        self, mock_save_cat, mock_save_sheet
    ):
        """Test CSV import reuses existing categories"""
        # Create existing category
        existing_cat = Category.objects.create(name="Food")
        Subcategory.objects.create(
            name="Groceries", category=existing_cat, skip_sheet_save=True
        )

        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        # Should not create duplicate category
        assert Category.objects.filter(name="Food").count() == 1
        assert Subcategory.objects.filter(name="Groceries").count() == 1

    @patch("trantrac.utils.save_to_sheet")
    def test_import_csv_save_failure(self, mock_save_sheet):
        """Test CSV import handles save_to_sheet failure"""
        mock_save_sheet.return_value = False

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is False
        assert "qualcosa è andato storto" in message

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_empty_subcategory(self, mock_save_cat, mock_save_sheet):
        """Test CSV import with empty subcategory"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = True

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        # Category should be created
        assert Category.objects.filter(name="Food").exists()
        # But no subcategory since it's empty
        assert not Subcategory.objects.filter(category__name="Food").exists()
