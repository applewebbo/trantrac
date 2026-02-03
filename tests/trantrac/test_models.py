from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import TestCase
from trantrac.models import Account, Category, CategoryUsage, Subcategory


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


@pytest.mark.django_db
class TestSaveCategoryAndSubToSheet:
    @patch("trantrac.models.build")
    @patch("trantrac.models.service_account.Credentials.from_service_account_info")
    def test_save_category_and_sub_to_sheet_success(self, mock_creds, mock_build):
        """Test save_category_and_sub_to_sheet returns True on success"""
        from trantrac.models import save_category_and_sub_to_sheet

        # Setup mocks
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 1}
        }

        result = save_category_and_sub_to_sheet([["Food", "Groceries"]])

        assert result is True
        mock_service.close.assert_called_once()

    @patch("trantrac.models.build")
    @patch("trantrac.models.service_account.Credentials.from_service_account_info")
    def test_save_category_and_sub_to_sheet_failure(self, mock_creds, mock_build):
        """Test save_category_and_sub_to_sheet returns False on failure"""
        from trantrac.models import save_category_and_sub_to_sheet

        # Setup mocks
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 0}
        }

        result = save_category_and_sub_to_sheet([["Food", "Groceries"]])

        assert result is False
        mock_service.close.assert_called_once()
