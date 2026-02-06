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


# telegram_bot fixtures


@pytest.fixture
def authenticated_user(test_user):
    """Create an authenticated user with telegram_chat_id"""
    test_user.telegram_chat_id = 12345
    test_user.phone_number = "+39123456789"
    test_user.save()
    return test_user


@pytest.fixture
def categories_setup(db):
    """Setup categories and subcategories for tests"""

    # Create categories
    alimentari = Category.objects.create(name="Alimentari")
    trasporti = Category.objects.create(name="Trasporti")
    casa = Category.objects.create(name="Casa")

    # Create subcategories
    bar = Subcategory.objects.create(
        name="Bar", category=alimentari, skip_sheet_save=True
    )
    supermercato = Subcategory.objects.create(
        name="Supermercato", category=alimentari, skip_sheet_save=True
    )
    ristorante = Subcategory.objects.create(
        name="Ristorante", category=alimentari, skip_sheet_save=True
    )
    carburante = Subcategory.objects.create(
        name="Carburante", category=trasporti, skip_sheet_save=True
    )
    parcheggio = Subcategory.objects.create(
        name="Parcheggio", category=trasporti, skip_sheet_save=True
    )
    affitto = Subcategory.objects.create(
        name="Affitto", category=casa, skip_sheet_save=True
    )

    # Create account
    test_account = Account.objects.create(name="Test User")

    return {
        "alimentari": alimentari,
        "trasporti": trasporti,
        "casa": casa,
        "bar": bar,
        "supermercato": supermercato,
        "ristorante": ristorante,
        "carburante": carburante,
        "parcheggio": parcheggio,
        "affitto": affitto,
        "account": test_account,
    }


@pytest.fixture
def category_usage_history(authenticated_user, categories_setup):
    """Create category usage history for testing suggestions"""
    from trantrac.models import CategoryUsage

    # User has used Bar 3 times
    for _ in range(3):
        CategoryUsage.objects.create(
            user=authenticated_user,
            category=categories_setup["alimentari"],
            subcategory=categories_setup["bar"],
        )

    # User has used Supermercato 1 time
    CategoryUsage.objects.create(
        user=authenticated_user,
        category=categories_setup["alimentari"],
        subcategory=categories_setup["supermercato"],
    )

    # User has used Carburante 2 times
    for _ in range(2):
        CategoryUsage.objects.create(
            user=authenticated_user,
            category=categories_setup["trasporti"],
            subcategory=categories_setup["carburante"],
        )
