from datetime import datetime, timezone

import pytest

from tests.conftest import TestCase
from trantrac.forms import (
    CategoryForm,
    CsvUploadForm,
    DateInput,
    SubcategoryForm,
    TransactionForm,
)
from trantrac.models import Account, Category, Subcategory


@pytest.mark.django_db
class TestDateInput(TestCase):
    def test_format_value_with_date_object(self):
        """Test format_value with datetime object"""
        widget = DateInput()
        date_obj = datetime(2025, 1, 15, tzinfo=timezone.utc)
        assert widget.format_value(date_obj) == "2025-01-15"

    def test_format_value_with_string(self):
        """Test format_value with string returns as is"""
        widget = DateInput()
        assert widget.format_value("2025-01-15") == "2025-01-15"

    def test_format_value_with_none(self):
        """Test format_value with None returns empty string"""
        widget = DateInput()
        assert widget.format_value(None) == ""

    def test_input_type_is_date(self):
        """Test input type is date"""
        widget = DateInput()
        assert widget.input_type == "date"


@pytest.mark.django_db
class TestTransactionForm(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")
        self.category = Category.objects.create(name="Food")
        self.subcategory = Subcategory.objects.create(
            name="Groceries", category=self.category, skip_sheet_save=True
        )
        self.account = Account.objects.create(name="Test Account")

    def test_valid_transaction_form(self):
        """Test valid transaction form"""
        data = {
            "amount": "100.50",
            "date": "2025-01-15",
            "description": "Test transaction",
            "category": self.category.id,
            "subcategory": self.subcategory.id,
            "bank_account": self.account.id,
        }
        form = TransactionForm(data=data, user=self.user)
        assert form.is_valid()

    def test_amount_must_be_positive(self):
        """Test amount must be greater than zero"""
        data = {
            "amount": "-10.00",
            "date": "2025-01-15",
            "description": "Test",
            "category": self.category.id,
            "subcategory": self.subcategory.id,
            "bank_account": self.account.id,
        }
        form = TransactionForm(data=data, user=self.user)
        assert not form.is_valid()
        assert "amount" in form.errors
        assert (
            "Il valore inserito deve essere maggiore di zero"
            in form.errors["amount"][0]
        )

    def test_amount_zero_is_invalid(self):
        """Test amount of zero is invalid"""
        data = {
            "amount": "0.00",
            "date": "2025-01-15",
            "description": "Test",
            "category": self.category.id,
            "subcategory": self.subcategory.id,
            "bank_account": self.account.id,
        }
        form = TransactionForm(data=data, user=self.user)
        assert not form.is_valid()

    def test_form_initializes_with_user_account(self):
        """Test form initializes bank_account based on user display_name"""
        user_account = Account.objects.create(name="Test User")
        form = TransactionForm(user=self.user)

        assert form.fields["bank_account"].initial == user_account

    def test_form_initializes_with_first_account_if_no_match(self):
        """Test form uses first account if no matching account"""
        user = self.make_user("other@example.com")
        form = TransactionForm(user=user)

        assert form.fields["bank_account"].initial == self.account

    def test_form_initializes_date_to_now(self):
        """Test form initializes date to current datetime"""
        form = TransactionForm(user=self.user)
        assert form.fields["date"].initial is not None

    def test_subcategory_queryset_filtered_by_category(self):
        """Test subcategory queryset is filtered when category is selected"""
        other_category = Category.objects.create(name="Transport")
        other_subcategory = Subcategory.objects.create(
            name="Bus", category=other_category, skip_sheet_save=True
        )

        data = {
            "category": self.category.id,
            "amount": "10",
            "date": "2025-01-15",
            "description": "Test",
            "bank_account": self.account.id,
        }
        form = TransactionForm(data=data, user=self.user)

        subcategories = form.fields["subcategory"].queryset
        assert self.subcategory in subcategories
        assert other_subcategory not in subcategories

    def test_subcategory_queryset_empty_when_no_category(self):
        """Test subcategory queryset is empty when no category selected"""
        form = TransactionForm(user=self.user)
        assert form.fields["subcategory"].queryset.count() == 0

    def test_form_handles_invalid_category_id(self):
        """Test form handles invalid category ID gracefully"""
        data = {
            "category": "invalid",
            "amount": "10",
            "date": "2025-01-15",
            "description": "Test",
            "bank_account": self.account.id,
        }
        form = TransactionForm(data=data, user=self.user)
        # Should not raise exception, just keep empty subcategory queryset
        assert form.fields["subcategory"].queryset.count() == 0

    def test_form_without_user(self):
        """Test form can be initialized without user"""
        form = TransactionForm()
        assert form.fields["bank_account"].initial == self.account


@pytest.mark.django_db
class TestCategoryForm(TestCase):
    def test_valid_category_form(self):
        """Test valid category form"""
        data = {"name": "New Category"}
        form = CategoryForm(data=data)
        assert form.is_valid()
        category = form.save()
        assert category.name == "New Category"

    def test_empty_category_name_invalid(self):
        """Test empty category name is invalid"""
        data = {"name": ""}
        form = CategoryForm(data=data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_category_form_has_helper(self):
        """Test category form has crispy forms helper"""
        form = CategoryForm()
        assert hasattr(form, "helper")
        assert not form.helper.form_tag


@pytest.mark.django_db
class TestSubcategoryForm(TestCase):
    def setUp(self):
        """Setup test data"""
        self.category = Category.objects.create(name="Food")

    def test_valid_subcategory_form(self):
        """Test valid subcategory form"""
        data = {"name": "New Subcategory", "category": self.category.id}
        form = SubcategoryForm(data=data)
        assert form.is_valid()

    def test_subcategory_form_with_initial_category(self):
        """Test subcategory form with initial category"""
        form = SubcategoryForm(initial={"category": self.category.id})
        assert form.initial["category"] == self.category.id

    def test_empty_subcategory_name_invalid(self):
        """Test empty subcategory name is invalid"""
        data = {"name": "", "category": self.category.id}
        form = SubcategoryForm(data=data)
        assert not form.is_valid()

    def test_subcategory_form_has_helper(self):
        """Test subcategory form has crispy forms helper"""
        form = SubcategoryForm()
        assert hasattr(form, "helper")
        assert not form.helper.form_tag


@pytest.mark.django_db
class TestCsvUploadForm(TestCase):
    def test_csv_upload_form_initialization(self):
        """Test CSV upload form initializes correctly"""
        form = CsvUploadForm()
        assert "csv_file" in form.fields
        assert form.fields["csv_file"].label is False

    def test_csv_upload_form_has_helper(self):
        """Test CSV upload form has crispy forms helper"""
        form = CsvUploadForm()
        assert hasattr(form, "helper")
        assert not form.helper.form_tag

    def test_clean_file_validates_csv_extension(self):
        """Test clean_file validates CSV file extension"""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Valid CSV file
        csv_file = SimpleUploadedFile("test.csv", b"data", content_type="text/csv")
        form = CsvUploadForm()
        form.cleaned_data = {"file": csv_file}
        assert form.clean_file() == csv_file

    def test_clean_file_rejects_non_csv(self):
        """Test clean_file rejects non-CSV files"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.forms import ValidationError

        # Invalid file extension
        txt_file = SimpleUploadedFile("test.txt", b"data", content_type="text/plain")
        form = CsvUploadForm()
        form.cleaned_data = {"file": txt_file}

        with pytest.raises(ValidationError, match="Il file deve essere in formato csv"):
            form.clean_file()
