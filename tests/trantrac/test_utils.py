from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile

from tests.conftest import TestCase
from trantrac.models import Category, Subcategory
from trantrac.utils import (
    _ensure_categories_in_db,
    delete_row_by_identifier,
    get_existing_transaction_ids,
    get_sheet_data,
    get_sheets_service,
    import_csv_to_sheet,
    sanitize_csv_value,
    save_to_sheet,
    smart_truncate,
)


@pytest.mark.django_db
class TestGetSheetsService:
    @patch("trantrac.models.GoogleSheetsSettings.get_settings")
    @patch("trantrac.utils.build")
    @patch("trantrac.utils.service_account.Credentials.from_service_account_info")
    def test_get_sheets_service_returns_service(
        self, mock_creds, mock_build, mock_get_settings
    ):
        """Test get_sheets_service returns Google Sheets service"""
        # Mock GoogleSheetsSettings
        mock_settings = MagicMock()
        mock_settings.get_credentials_dict.return_value = {
            "type": "service_account",
            "project_id": "test-project",
        }
        mock_get_settings.return_value = mock_settings

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        service = get_sheets_service()

        assert service == mock_service
        mock_build.assert_called_once()

    @patch("trantrac.models.GoogleSheetsSettings.get_settings")
    @patch("trantrac.utils.build")
    @patch("trantrac.utils.service_account.Credentials.from_service_account_info")
    def test_get_sheets_service_uses_db_settings(
        self, mock_creds, mock_build, mock_get_settings
    ):
        """Test get_sheets_service uses settings from database"""
        # Mock GoogleSheetsSettings
        mock_settings = MagicMock()
        mock_settings.get_credentials_dict.return_value = {
            "type": "service_account",
            "project_id": "test-project",
            "client_email": "test@example.com",
        }
        mock_get_settings.return_value = mock_settings

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        service = get_sheets_service()

        # Verify get_credentials_dict was called
        mock_settings.get_credentials_dict.assert_called_once()
        # Verify credentials were created from the dict
        mock_creds.assert_called_once()
        assert service == mock_service


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

        assert result == (True, "")

    @patch("trantrac.utils.get_sheets_service")
    def test_save_to_sheet_failure(self, mock_get_service):
        """Test save_to_sheet returns (False, "") on failure"""
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

        assert result == (False, "")

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

    @patch("trantrac.utils.get_sheets_service")
    def test_save_to_sheet_returns_false_on_exception(self, mock_get_service):
        """Test save_to_sheet returns False when API raises an exception"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets().values().get().execute.side_effect = Exception(
            "API error"
        )

        result = save_to_sheet([["row"]], "USCITE")

        assert result == (False, "")
        mock_service.close.assert_called_once()


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
class TestGetExistingTransactionIds:
    @patch("trantrac.utils.get_sheets_service")
    def test_returns_ids_from_both_sheets(self, mock_get_service):
        """Test that IDs are collected from ENTRATE and USCITE"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().batchGet().execute.return_value = {
            "valueRanges": [
                {"values": [["ABC123"], ["DEF456"]]},
                {"values": [["GHI789"], ["JKL012"]]},
            ]
        }

        result = get_existing_transaction_ids()

        assert result == {"ABC123", "DEF456", "GHI789", "JKL012"}
        mock_service.close.assert_called_once()

    @patch("trantrac.utils.get_sheets_service")
    def test_returns_empty_set_when_no_data(self, mock_get_service):
        """Test that empty set is returned when sheets are empty"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().batchGet().execute.return_value = {
            "valueRanges": []
        }

        result = get_existing_transaction_ids()

        assert result == set()

    @patch("trantrac.utils.get_sheets_service")
    def test_ignores_empty_rows(self, mock_get_service):
        """Test that empty rows are ignored"""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().batchGet().execute.return_value = {
            "valueRanges": [
                {"values": [["ABC123"], [], ["DEF456"]]},
            ]
        }

        result = get_existing_transaction_ids()

        assert result == {"ABC123", "DEF456"}


@pytest.mark.django_db
class TestImportCsvToSheet(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")
        patcher = patch(
            "trantrac.utils.get_existing_transaction_ids", return_value=set()
        )
        patcher.start()
        self.addCleanup(patcher.stop)

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
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123
02/01/2025,+500.00,ENRICO Test Income,Salary,,DEF456"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        assert "Importate 2 transazioni" in message

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
        mock_save_sheet.return_value = (True, "")

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
        mock_save_sheet.return_value = (True, "")

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
        mock_save_sheet.return_value = (True, "")

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
        """Test CSV import detects user names via configurable UserMapping"""
        from trantrac.models import UserMapping

        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        UserMapping.objects.create(keyword="VIVIANA", display_name="Viviana", order=0)
        UserMapping.objects.create(keyword="ENRICO", display_name="Enrico", order=1)
        UserMapping.objects.create(keyword="APPLE", display_name="Enrico", order=2)

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
        mock_save_sheet.return_value = (True, "")

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
    def test_import_csv_truncates_long_descriptions_uscite(
        self, mock_save_cat, mock_save_sheet
    ):
        """USCITE always use standard truncation to 50 chars"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        long_desc = "A" * 60
        csv_content = f"""Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,{long_desc},Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        uscite_call = [
            call for call in mock_save_sheet.call_args_list if call[0][1] == "USCITE"
        ][0]
        description = uscite_call[0][0][0][3]

        assert len(description) == 50
        assert description.endswith("...")

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_smart_truncate_entrate_with_config(
        self, mock_save_cat, mock_save_sheet
    ):
        """ENTRATE use smart truncation when IncomeParsingConfig is active."""
        from trantrac.models import IncomeParsingConfig

        IncomeParsingConfig.objects.create(enabled=True, trigger_string="DA ")
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        long_desc = "ASSEGNO UNICO PER 1 FIGLI/O PER IL PERIODO DA 01-04-2026 A 30-04-2026 - NUMERO PRATICA 16961 DA INPS"
        csv_content = f"""Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,+500.00,{long_desc},Entrate,Stipendio,XYZ456"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        entrate_call = [
            call for call in mock_save_sheet.call_args_list if call[0][1] == "ENTRATE"
        ][0]
        description = entrate_call[0][0][0][3]

        assert description.endswith("DA INPS")
        assert "..." in description

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_entrate_standard_truncation_without_config(
        self, mock_save_cat, mock_save_sheet
    ):
        """ENTRATE use standard truncation when IncomeParsingConfig is disabled or absent."""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        long_desc = "A" * 60
        csv_content = f"""Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,+500.00,{long_desc},Entrate,Stipendio,XYZ456"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        entrate_call = [
            call for call in mock_save_sheet.call_args_list if call[0][1] == "ENTRATE"
        ][0]
        description = entrate_call[0][0][0][3]

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
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        import_csv_to_sheet(csv_file, self.user)

        # Should not create duplicate category
        assert Category.objects.filter(name="Food").count() == 1
        assert Subcategory.objects.filter(name="Groceries").count() == 1

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_save_failure(self, mock_save_cat, mock_save_sheet):
        """Test CSV import handles save_to_sheet failure"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (False, "")

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
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        # Category should be created
        assert Category.objects.filter(name="Food").exists()
        # But no subcategory since it's empty
        assert not Subcategory.objects.filter(category__name="Food").exists()

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_continues_if_category_sync_fails(
        self, mock_save_cat, mock_save_sheet
    ):
        """Test CSV import continues even if category sheet sync raises exception"""
        mock_save_cat.side_effect = Exception("Sheets API error")
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        # Import should succeed even if sync fails
        assert success is True

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_import_csv_skips_intra_file_duplicates(
        self, mock_save_cat, mock_save_sheet
    ):
        """Rows with the same Codice identificativo within the same CSV are skipped"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,First occurrence,Food,Groceries,SAME123
02/01/2025,-50.00,Duplicate in file,Food,Groceries,SAME123
03/01/2025,-30.00,Different row,Food,Groceries,OTHER456"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        assert "Importate 2 transazioni" in message
        assert "1 duplicate saltate" in message

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    @patch(
        "trantrac.utils.get_existing_transaction_ids", return_value={"ABC123", "DEF456"}
    )
    def test_import_csv_skips_duplicate_ids(
        self, mock_existing, mock_save_cat, mock_save_sheet
    ):
        """Test that rows with already-imported Codice identificativo are skipped"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Already imported,Food,Groceries,ABC123
02/01/2025,-50.00,New transaction,Food,Groceries,GHI789
03/01/2025,+200.00,Also imported,Salary,,DEF456"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        assert "Importate 1 transazioni" in message
        assert "2 duplicate saltate" in message

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    @patch("trantrac.utils.get_existing_transaction_ids", return_value={"XYZ999"})
    def test_import_csv_empty_id_not_skipped(
        self, mock_existing, mock_save_cat, mock_save_sheet
    ):
        """Test that rows with empty Codice identificativo are never skipped"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")

        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,No ID transaction,Food,Groceries,"""

        csv_file = self.create_csv_file(csv_content)
        success, message = import_csv_to_sheet(csv_file, self.user)

        assert success is True
        assert "Importate 1 transazioni" in message
        assert "duplicate" not in message


@pytest.mark.django_db
class TestEnsureCategoriesInDb:
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_creates_new_category_and_subcategory(self, mock_save):
        """Creates missing category and subcategory in DB"""
        mock_save.return_value = True
        _ensure_categories_in_db({("Food", "Groceries")})
        from trantrac.models import Category, Subcategory

        assert Category.objects.filter(name="Food").exists()
        assert Subcategory.objects.filter(name="Groceries").exists()

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_reuses_existing_category(self, mock_save):
        """Does not create duplicate category"""
        from trantrac.models import Category

        Category.objects.create(name="Food")
        _ensure_categories_in_db({("Food", "Groceries")})
        assert Category.objects.filter(name="Food").count() == 1

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_skips_empty_subcategory(self, mock_save):
        """Does not create subcategory when name is empty"""
        from trantrac.models import Subcategory

        _ensure_categories_in_db({("Food", "")})
        assert not Subcategory.objects.filter(category__name="Food").exists()
        mock_save.assert_not_called()

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_syncs_new_subcategories_to_sheets(self, mock_save):
        """Calls save_category_and_sub_to_sheet for new subcategories"""
        mock_save.return_value = True
        _ensure_categories_in_db({("Food", "Groceries")})
        mock_save.assert_called_once()

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_continues_if_sheet_sync_fails(self, mock_save):
        """DB records are created even if Sheets sync raises"""
        mock_save.side_effect = Exception("API error")
        _ensure_categories_in_db({("Food", "Groceries")})
        from trantrac.models import Category

        assert Category.objects.filter(name="Food").exists()

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_reuses_existing_subcategory(self, mock_save):
        """Does not create duplicate subcategory"""
        from trantrac.models import Category, Subcategory

        cat = Category.objects.create(name="Food")
        Subcategory.objects.create(name="Groceries", category=cat, skip_sheet_save=True)
        _ensure_categories_in_db({("Food", "Groceries")})
        assert Subcategory.objects.filter(name="Groceries").count() == 1
        mock_save.assert_not_called()


class TestSmartTruncate:
    def test_short_string_unchanged(self):
        assert smart_truncate("VOCIRETRIB.", 50) == "VOCIRETRIB."

    def test_standard_truncation_without_trigger(self):
        result = smart_truncate("A" * 60, 50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_standard_truncation_trigger_not_found(self):
        long = "PAGAMENTO UTENZA GAS APRILE 2025 NUMERO CONTRATTO 1234567890"
        result = smart_truncate(long, 50, trigger="DA ")
        assert result.endswith("...")
        assert len(result) == 50

    def test_smart_truncation_preserves_trigger_suffix(self):
        desc = "ASSEGNO UNICO PER 1 FIGLI/O PER IL PERIODO DA 01-04-2026 A 30-04-2026 - NUMERO PRATICA 16961 DA INPS"
        result = smart_truncate(desc, 50, trigger="DA ")
        assert result.endswith("DA INPS")
        assert "..." in result
        assert len(result) <= 50

    def test_smart_truncation_uses_last_trigger(self):
        desc = "DA 01-04-2026 A 30-04-2026 - NUMERO PRATICA 16961 DA INPS"
        result = smart_truncate(desc, 50, trigger="DA ")
        assert result.endswith("DA INPS")

    def test_does_not_match_trigger_inside_word(self):
        desc = "DA MARIO BIANCHI SPESE VARIE MESE CORRENTE ANNO"
        result = smart_truncate(desc, 50, trigger="DA")
        assert (
            result.endswith("DA MARIO BIANCHI SPESE VARIE MESE CORRENTE ANNO")
            or "ARIO" not in result
        )

    def test_smart_truncation_with_empty_trigger(self):
        long = "A" * 60
        result = smart_truncate(long, 50, trigger="")
        assert result.endswith("...")

    def test_smart_truncation_suffix_longer_than_max(self):
        # "DA " preceded by space so \bDA\b matches; suffix alone > max_len
        desc = "ACCREDITO DA " + "Y" * 60
        result = smart_truncate(desc, 50, trigger="DA ")
        assert result.startswith("...")
        assert "DA " in result

    def test_exact_max_length_unchanged(self):
        desc = "A" * 50
        assert smart_truncate(desc, 50) == desc


class TestSanitizeCsvValue:
    def test_strips_leading_equals(self):
        assert sanitize_csv_value("=SUM(1,2)") == "SUM(1,2)"

    def test_strips_leading_plus(self):
        assert sanitize_csv_value("+cmd|calc") == "cmd|calc"

    def test_strips_leading_at(self):
        assert sanitize_csv_value("@SUM(1)") == "SUM(1)"

    def test_leaves_normal_text_unchanged(self):
        assert sanitize_csv_value("Prelievo ATM") == "Prelievo ATM"

    def test_strips_surrounding_whitespace(self):
        assert sanitize_csv_value("  hello  ") == "hello"

    def test_does_not_strip_leading_dash(self):
        assert sanitize_csv_value("-prestito") == "-prestito"

    def test_empty_string(self):
        assert sanitize_csv_value("") == ""


@pytest.mark.django_db
class TestImportCsvValidations(TestCase):
    def setUp(self):
        self.user = self.make_user("test@example.com")
        patcher = patch(
            "trantrac.utils.get_existing_transaction_ids", return_value=set()
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def create_csv_file(self, content):
        csv_bytes = content.encode("utf-8")
        return InMemoryUploadedFile(
            BytesIO(csv_bytes),
            "csv_file",
            "test.csv",
            "text/csv",
            len(csv_bytes),
            "utf-8",
        )

    @patch("trantrac.utils.save_to_sheet")
    def test_invalid_date_returns_error(self, mock_save_sheet):
        """Invalid date format returns False with descriptive message"""
        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
31-13-2025,-100.50,Test,Food,Groceries,ABC123"""
        success, message = import_csv_to_sheet(
            self.create_csv_file(csv_content), self.user
        )
        assert success is False
        assert "Data non valida" in message
        assert "gg/mm/aaaa" in message

    @patch("trantrac.utils.save_to_sheet")
    def test_amount_over_limit_returns_error(self, mock_save_sheet):
        """Amount exceeding MAX_TRANSACTION_AMOUNT returns False"""
        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-1500000,Test,Food,Groceries,ABC123"""
        success, message = import_csv_to_sheet(
            self.create_csv_file(csv_content), self.user
        )
        assert success is False
        assert "Importo troppo grande" in message

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_sanitizes_formula_injection_in_description(
        self, mock_save_cat, mock_save_sheet
    ):
        """Description starting with = is sanitized before saving to sheet"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")
        csv_content = """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,=SUM(1+2),Food,Groceries,ABC123"""
        import_csv_to_sheet(self.create_csv_file(csv_content), self.user)
        uscite_call = [
            c for c in mock_save_sheet.call_args_list if c[0][1] == "USCITE"
        ][0]
        description = uscite_call[0][0][0][3]
        assert not description.startswith("=")

    @patch("trantrac.utils.save_to_sheet")
    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_truncates_long_category_names(self, mock_save_cat, mock_save_sheet):
        """Category names longer than 100 chars are truncated"""
        mock_save_cat.return_value = True
        mock_save_sheet.return_value = (True, "")
        long_cat = "A" * 150
        csv_content = f"""Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test,{long_cat},,ABC123"""
        import_csv_to_sheet(self.create_csv_file(csv_content), self.user)
        from trantrac.models import Category

        cat = Category.objects.filter(name__startswith="A" * 50).first()
        assert cat is not None
        assert len(cat.name) <= 100


@pytest.mark.django_db
class TestDeleteRowByIdentifier:
    @patch("trantrac.utils.get_sheets_service")
    def test_deletes_matching_row(self, mock_get_service):
        """Test that the correct row is deleted when identifier is found."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        # Column H has: header, AAAAAA-BOT, BBBBBB-BOT
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["header"], ["AAAAAA-BOT"], ["BBBBBB-BOT"]]
        }
        mock_service.spreadsheets().get().execute.return_value = {
            "sheets": [{"properties": {"title": "USCITE", "sheetId": 42}}]
        }

        result = delete_row_by_identifier("USCITE", "BBBBBB-BOT", 7)

        assert result is True
        batch_call = mock_service.spreadsheets().batchUpdate.call_args[1]["body"]
        delete_req = batch_call["requests"][0]["deleteDimension"]["range"]
        assert delete_req["startIndex"] == 2  # row index 2 (BBBBBB-BOT)
        assert delete_req["endIndex"] == 3

    @patch("trantrac.utils.get_sheets_service")
    def test_raises_when_identifier_not_found(self, mock_get_service):
        """Test that ValueError is raised when identifier is not in the sheet."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [["AAAAAA-BOT"], ["BBBBBB-BOT"]]
        }

        with pytest.raises(ValueError, match="not found"):
            delete_row_by_identifier("USCITE", "ZZZZZZ-BOT", 7)

    @patch("trantrac.utils.get_sheets_service")
    def test_raises_when_sheet_empty(self, mock_get_service):
        """Test that ValueError is raised when the sheet has no data."""
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        mock_service.spreadsheets().values().get().execute.return_value = {}

        with pytest.raises(ValueError, match="not found"):
            delete_row_by_identifier("USCITE", "AAAAAA-BOT", 7)
