"""Shared fixtures for telegram_bot tests"""

from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.utils import timezone

from telegram_bot.models import TelegramAuthSession
from trantrac.models import Account, Category, CategoryUsage, Subcategory
from users.models import User


@pytest.fixture
def user(db):
    """Create a test user"""
    return User.objects.create(
        email="test@example.com",
        display_name="Test User",
    )


@pytest.fixture
def authenticated_user(user):
    """Create an authenticated user with telegram_chat_id"""
    user.telegram_chat_id = 12345
    user.phone_number = "+39123456789"
    user.save()
    return user


@pytest.fixture
def categories_setup(db):
    """Setup categories and subcategories for tests"""
    # Create categories
    alimentari = Category.objects.create(name="Alimentari")
    trasporti = Category.objects.create(name="Trasporti")
    casa = Category.objects.create(name="Casa")

    # Create subcategories
    bar = Subcategory.objects.create(name="Bar", category=alimentari)
    supermercato = Subcategory.objects.create(name="Supermercato", category=alimentari)
    ristorante = Subcategory.objects.create(name="Ristorante", category=alimentari)
    carburante = Subcategory.objects.create(name="Carburante", category=trasporti)
    parcheggio = Subcategory.objects.create(name="Parcheggio", category=trasporti)
    affitto = Subcategory.objects.create(name="Affitto", category=casa)

    # Create account
    account = Account.objects.create(name="Test User")

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
        "account": account,
    }


@pytest.fixture
def category_usage_history(authenticated_user, categories_setup):
    """Create category usage history for testing suggestions"""
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


@pytest.fixture
def auth_session(db):
    """Create a test auth session"""
    return TelegramAuthSession.objects.create(
        chat_id=12345,
        phone_number="+39123456789",
    )


@pytest.fixture
def expired_auth_session(db):
    """Create an expired auth session"""
    session = TelegramAuthSession.objects.create(
        chat_id=67890,
        phone_number="+39987654321",
    )
    # Make it expired (older than 5 minutes)
    session.created_at = timezone.now() - timedelta(minutes=10)
    session.save()
    return session


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram Update object"""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 12345
    update.message = MagicMock()
    update.message.message_id = 1
    update.message.text = ""
    update.message.reply_text = MagicMock()
    update.message.contact = None
    return update


@pytest.fixture
def mock_telegram_context():
    """Create a mock Telegram CallbackContext"""
    context = MagicMock()
    context.user_data = {}
    return context
