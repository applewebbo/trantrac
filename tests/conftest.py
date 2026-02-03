from unittest.mock import MagicMock, patch

import pytest
from test_plus import TestCase as BaseTestCase

from trantrac.models import Account, Category, Subcategory
from users.models import User

from .factories import UserFactory


class TestCase(BaseTestCase):
    """Custom TestCase configured with UserFactory for our email-based User model"""

    user_factory = UserFactory


@pytest.fixture
def test_user(db):
    """Create a test user"""
    return User.objects.create_user(
        email="test@example.com", password="password", display_name="Test User"
    )


@pytest.fixture
def create_user(db):
    """Factory fixture to create users with custom parameters"""

    def _create_user(**kwargs):
        email = kwargs.pop("email", "user@example.com")
        password = kwargs.pop("password", "password")
        return User.objects.create_user(email=email, password=password, **kwargs)

    return _create_user


@pytest.fixture
def category():
    """Create test category"""
    return Category.objects.create(name="Test Category")


@pytest.fixture
def subcategory(category):
    """Create test subcategory"""
    return Subcategory.objects.create(
        name="Test Subcategory", category=category, skip_sheet_save=True
    )


@pytest.fixture
def account():
    """Create test account"""
    return Account.objects.create(name="Test Account")


@pytest.fixture
def tp():
    """TestPlus helper instance"""
    from test_plus import TestCase

    return TestCase()


@pytest.fixture
def mock_sheets_service():
    """Mock Google Sheets service"""
    with patch("trantrac.utils.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock get response
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}

        # Mock append response
        mock_service.spreadsheets().values().append().execute.return_value = {
            "updates": {"updatedRows": 1}
        }

        yield mock_service


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for import testing"""
    return """Data operazione,Importo,Descrizione,Categoria,Sottocategoria,Codice identificativo
01/01/2025,-100.50,Test Transaction,Food,Groceries,ABC123
02/01/2025,+500.00,ENRICO Test Income,Salary,,DEF456
03/01/2025,-50.25,Another Transaction,Transport,Bus,GHI789"""
