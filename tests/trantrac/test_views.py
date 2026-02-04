from unittest.mock import patch

import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from tests.conftest import TestCase
from trantrac.models import Account, Category, CategoryUsage, Subcategory
from trantrac.views import get_most_used_categories, get_recent_categories


@pytest.mark.django_db
class TestGetRecentCategories(TestCase):
    def test_get_recent_categories_returns_last_used(self):
        """Test get_recent_categories returns most recent category usage"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")
        subcategory = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )

        # Create multiple usages
        CategoryUsage.objects.create(
            user=user, category=category, subcategory=subcategory
        )
        CategoryUsage.objects.create(
            user=user, category=category, subcategory=subcategory
        )

        result = get_recent_categories(limit=6)
        assert len(result) == 1
        assert result[0]["category"] == category.id
        assert result[0]["subcategory"] == subcategory.id

    def test_get_recent_categories_respects_limit(self):
        """Test get_recent_categories respects limit parameter"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")

        # Create multiple subcategories
        for i in range(10):
            subcategory = Subcategory.objects.create(
                name=f"Sub{i}", category=category, skip_sheet_save=True
            )
            CategoryUsage.objects.create(
                user=user, category=category, subcategory=subcategory
            )

        result = get_recent_categories(limit=3)
        assert len(result) == 3


@pytest.mark.django_db
class TestGetMostUsedCategories(TestCase):
    def test_get_most_used_categories_returns_top_used(self):
        """Test get_most_used_categories returns most used categories"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")
        subcategory1 = Subcategory.objects.create(
            name="Groceries", category=category, skip_sheet_save=True
        )
        subcategory2 = Subcategory.objects.create(
            name="Restaurant", category=category, skip_sheet_save=True
        )

        # Create more usages for subcategory1
        for _ in range(5):
            CategoryUsage.objects.create(
                user=user, category=category, subcategory=subcategory1
            )

        for _ in range(2):
            CategoryUsage.objects.create(
                user=user, category=category, subcategory=subcategory2
            )

        result = get_most_used_categories(limit=6)
        assert len(result) == 2
        # First should be the most used
        assert result[0]["subcategory"] == subcategory1.id
        assert result[1]["subcategory"] == subcategory2.id

    def test_get_most_used_categories_respects_limit(self):
        """Test get_most_used_categories respects limit parameter"""
        user = self.make_user("test@example.com")
        category = Category.objects.create(name="Food")

        for i in range(10):
            subcategory = Subcategory.objects.create(
                name=f"Sub{i}", category=category, skip_sheet_save=True
            )
            CategoryUsage.objects.create(
                user=user, category=category, subcategory=subcategory
            )

        result = get_most_used_categories(limit=3)
        assert len(result) == 3


@pytest.mark.django_db
class TestIndexView(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")
        self.category = Category.objects.create(name="Food")
        self.subcategory = Subcategory.objects.create(
            name="Groceries", category=self.category, skip_sheet_save=True
        )
        self.account = Account.objects.create(name="Test User")

    def test_index_get_request(self):
        """Test index view GET request"""
        with self.login(username=self.user.email, password="password"):
            response = self.get("index")

        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/index.html")
        assert "form" in response.context
        assert "recent_categories" in response.context
        assert "most_used_categories" in response.context

    @patch("trantrac.views.save_to_sheet")
    def test_index_post_valid_transaction(self, mock_save):
        """Test index view POST with valid transaction"""
        mock_save.return_value = True

        with self.login(username=self.user.email, password="password"):
            response = self.post(
                "index",
                data={
                    "amount": "100.50",
                    "date": "2025-01-15",
                    "description": "Test transaction",
                    "category": self.category.id,
                    "subcategory": self.subcategory.id,
                    "bank_account": self.account.id,
                },
            )

        assert response.status_code == 204
        assert response.headers.get("HX-Refresh") == "true"

        # Check category usage was created
        assert CategoryUsage.objects.filter(
            user=self.user, category=self.category, subcategory=self.subcategory
        ).exists()

    @patch("trantrac.views.save_to_sheet")
    def test_index_post_save_failure(self, mock_save):
        """Test index view POST when save_to_sheet fails"""
        mock_save.return_value = False

        with self.login(username=self.user.email, password="password"):
            response = self.post(
                "index",
                data={
                    "amount": "100.50",
                    "date": "2025-01-15",
                    "description": "Test transaction",
                    "category": self.category.id,
                    "subcategory": self.subcategory.id,
                    "bank_account": self.account.id,
                },
            )

        messages = list(get_messages(response.wsgi_request))
        assert any("qualcosa è andato storto" in str(m) for m in messages)

    def test_index_htmx_request(self):
        """Test index view with HTMX request"""
        with self.login(username=self.user.email, password="password"):
            response = self.get("index", extra={"HTTP_HX_REQUEST": "true"})

        self.assertTemplateUsed(response, "trantrac/transaction_form.html")

    def test_index_requires_login(self):
        """Test index view requires authentication"""
        response = self.get("index")
        assert response.status_code == 302

    @patch("trantrac.views.save_to_sheet")
    def test_index_post_invalid_form(self, mock_save):
        """Test index view POST with invalid form data"""
        with self.login(username=self.user.email, password="password"):
            response = self.post(
                "index",
                data={
                    "amount": "-10.00",  # Invalid negative amount
                    "date": "2025-01-15",
                    "description": "Test",
                    "category": self.category.id,
                    "subcategory": self.subcategory.id,
                    "bank_account": self.account.id,
                },
            )

        # Should return 200 with form errors, not 204
        assert response.status_code == 200
        # save_to_sheet should not be called for invalid form
        mock_save.assert_not_called()


@pytest.mark.django_db
class TestAddCategoryView(TestCase):
    def test_add_category_get(self):
        """Test add_category view GET request"""
        response = self.get("add_category")
        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/add_category.html")

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_add_category_post_valid(self, mock_save):
        """Test add_category view POST with valid data"""
        mock_save.return_value = True

        response = self.post("add_category", data={"name": "New Category"})

        assert response.status_code == 302
        assert response.url == reverse("index")
        assert Category.objects.filter(name="New Category").exists()

    def test_add_category_post_invalid(self):
        """Test add_category view POST with invalid data"""
        response = self.post("add_category", data={"name": ""})

        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/add_category.html")


@pytest.mark.django_db
class TestAddSubcategoryView(TestCase):
    def setUp(self):
        """Setup test data"""
        self.category = Category.objects.create(name="Food")

    def test_add_subcategory_get(self):
        """Test add_subcategory view GET request"""
        response = self.get("add_subcategory")
        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/add_subcategory.html")

    def test_add_subcategory_get_with_category_param(self):
        """Test add_subcategory view GET with category parameter"""
        response = self.get("add_subcategory", data={"category": self.category.id})
        assert response.status_code == 200
        assert response.context["form"].initial["category"] == str(self.category.id)

    @patch("trantrac.models.save_category_and_sub_to_sheet")
    def test_add_subcategory_post_valid(self, mock_save):
        """Test add_subcategory view POST with valid data"""
        mock_save.return_value = True

        response = self.post(
            "add_subcategory",
            data={"name": "New Subcategory", "category": self.category.id},
        )

        assert response.status_code == 302
        assert response.url == reverse("index")
        assert Subcategory.objects.filter(name="New Subcategory").exists()

    def test_add_subcategory_post_invalid(self):
        """Test add_subcategory view POST with invalid data"""
        response = self.post("add_subcategory", data={"name": "", "category": ""})

        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/add_subcategory.html")


@pytest.mark.django_db
class TestUploadCsvView(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")

    def test_upload_csv_get(self):
        """Test upload_csv view GET request"""
        with self.login(username=self.user.email, password="password"):
            response = self.get("upload_csv")

        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/upload_csv_page.html")

    def test_upload_csv_get_htmx(self):
        """Test upload_csv view GET with HTMX request"""
        with self.login(username=self.user.email, password="password"):
            response = self.get("upload_csv", extra={"HTTP_HX_REQUEST": "true"})

        self.assertTemplateUsed(response, "trantrac/upload_csv.html")

    def test_upload_csv_requires_login(self):
        """Test upload_csv view requires authentication"""
        response = self.get("upload_csv")
        assert response.status_code == 302

    @patch("trantrac.views.import_csv_to_sheet")
    def test_upload_csv_post_success(self, mock_import):
        """Test upload_csv view POST with successful import"""
        mock_import.return_value = (True, "File importato con successo")

        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_content = b"Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo\n"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        with self.login(username=self.user.email, password="password"):
            response = self.post("upload_csv", data={"csv_file": csv_file})

        assert response.status_code == 204
        assert response.headers.get("HX-Redirect") == reverse("index")

    @patch("trantrac.views.import_csv_to_sheet")
    def test_upload_csv_post_failure(self, mock_import):
        """Test upload_csv view POST with failed import"""
        mock_import.return_value = (False, "Error importing file")

        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_content = b"invalid data"
        csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

        with self.login(username=self.user.email, password="password"):
            response = self.post("upload_csv", data={"csv_file": csv_file})

        messages = list(get_messages(response.wsgi_request))
        assert any("Error importing file" in str(m) for m in messages)

    def test_upload_csv_post_invalid_form(self):
        """Test upload_csv view POST with invalid form (missing file)"""
        with self.login(username=self.user.email, password="password"):
            response = self.post("upload_csv", data={})

        # Should return 200 with form, not redirect
        assert response.status_code == 200
        assert "form" in response.context


@pytest.mark.django_db
class TestLoadSubcategoriesView(TestCase):
    def setUp(self):
        """Setup test data"""
        self.category = Category.objects.create(name="Food")
        self.subcategory = Subcategory.objects.create(
            name="Groceries", category=self.category, skip_sheet_save=True
        )

    def test_load_subcategories_with_category(self):
        """Test load_subcategories view with category parameter"""
        response = self.get("load_subcategories", data={"category": self.category.id})

        assert response.status_code == 200
        self.assertTemplateUsed(response, "trantrac/subcategory_choices.html")
        assert self.subcategory in response.context["subcategories"]

    def test_load_subcategories_without_category(self):
        """Test load_subcategories view without category parameter"""
        response = self.get("load_subcategories")

        assert response.status_code == 200
        assert response.context["subcategories"].count() == 0

    def test_load_subcategories_filters_by_category(self):
        """Test load_subcategories only returns subcategories for selected category"""
        other_category = Category.objects.create(name="Transport")
        other_subcategory = Subcategory.objects.create(
            name="Bus", category=other_category, skip_sheet_save=True
        )

        response = self.get("load_subcategories", data={"category": self.category.id})

        subcategories = response.context["subcategories"]
        assert self.subcategory in subcategories
        assert other_subcategory not in subcategories


@pytest.mark.django_db
class TestRefreshCategoriesView(TestCase):
    def setUp(self):
        """Setup test data"""
        self.user = self.make_user("test@example.com")

    @patch("trantrac.views.get_sheet_data")
    def test_refresh_categories_success(self, mock_get_data):
        """Test refresh_categories view with successful data fetch"""
        mock_get_data.return_value = [["Food", "Groceries"], ["Transport", "Bus"]]

        with self.login(username=self.user.email, password="password"):
            response = self.get("refresh_categories")

        assert response.status_code == 204
        assert response.headers.get("HX-Redirect") == reverse("index")

        # Check categories and subcategories were created
        assert Category.objects.filter(name="Food").exists()
        assert Category.objects.filter(name="Transport").exists()
        assert Subcategory.objects.filter(name="Groceries").exists()
        assert Subcategory.objects.filter(name="Bus").exists()

    @patch("trantrac.views.get_sheet_data")
    def test_refresh_categories_no_data(self, mock_get_data):
        """Test refresh_categories view when no data is fetched"""
        mock_get_data.return_value = None

        with self.login(username=self.user.email, password="password"):
            response = self.get("refresh_categories")

        messages = list(get_messages(response.wsgi_request))
        assert any("Impossibile recuperare i dati" in str(m) for m in messages)

    @patch("trantrac.views.get_sheet_data")
    def test_refresh_categories_creates_only_new_items(self, mock_get_data):
        """Test refresh_categories doesn't duplicate existing categories"""
        # Create existing category
        existing_cat = Category.objects.create(name="Food")
        Subcategory.objects.create(
            name="Groceries", category=existing_cat, skip_sheet_save=True
        )

        mock_get_data.return_value = [["Food", "Groceries"], ["Transport", "Bus"]]

        with self.login(username=self.user.email, password="password"):
            self.get("refresh_categories")

        # Should not create duplicates
        assert Category.objects.filter(name="Food").count() == 1
        assert Subcategory.objects.filter(name="Groceries").count() == 1

        # Should create new ones
        assert Category.objects.filter(name="Transport").exists()
        assert Subcategory.objects.filter(name="Bus").exists()

    @patch("trantrac.views.get_sheet_data")
    def test_refresh_categories_handles_incomplete_rows(self, mock_get_data):
        """Test refresh_categories handles rows with missing subcategory"""
        mock_get_data.return_value = [["Food", "Groceries"], ["Transport"], []]

        with self.login(username=self.user.email, password="password"):
            self.get("refresh_categories")

        # Should create all valid categories
        assert Category.objects.filter(name="Food").exists()
        assert Category.objects.filter(name="Transport").exists()

        # Should only create subcategory where data exists
        assert Subcategory.objects.filter(name="Groceries").exists()
        assert Subcategory.objects.count() == 1

    def test_refresh_categories_requires_login(self):
        """Test refresh_categories view requires authentication"""
        response = self.get("refresh_categories")
        assert response.status_code == 302
