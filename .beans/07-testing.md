# Testing Strategy

## Test Structure

```
telegram_bot/tests/
├── __init__.py
├── conftest.py           # Fixtures condivise
├── test_parsers.py       # Unit tests parsing
├── test_suggestions.py   # Unit tests suggerimenti
├── test_auth.py          # Integration tests autenticazione
├── test_handlers.py      # Integration tests handlers
└── test_commands.py      # Tests management commands
```

## Fixtures (conftest.py)

```python
import pytest
from users.models import User
from trantrac.models import Category, Subcategory, Account

@pytest.fixture
def user():
    return User.objects.create(
        email="test@example.com",
        display_name="Test User"
    )

@pytest.fixture
def authenticated_user(user):
    user.telegram_chat_id = 12345
    user.phone_number = "+39123456789"
    user.save()
    return user

@pytest.fixture
def categories_setup():
    """Setup categorie e sottocategorie per test"""
    alimentari = Category.objects.create(name="Alimentari")
    trasporti = Category.objects.create(name="Trasporti")

    bar = Subcategory.objects.create(name="Bar", category=alimentari)
    supermercato = Subcategory.objects.create(name="Supermercato", category=alimentari)
    carburante = Subcategory.objects.create(name="Carburante", category=trasporti)

    account = Account.objects.create(name="Test User")

    return {
        'alimentari': alimentari,
        'trasporti': trasporti,
        'bar': bar,
        'supermercato': supermercato,
        'carburante': carburante,
        'account': account,
    }

@pytest.fixture
def mock_update():
    """Mock Telegram Update object"""
    from unittest.mock import MagicMock
    from telegram import Update, Message, Chat, User as TgUser

    update = MagicMock(spec=Update)
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 12345
    update.message = MagicMock(spec=Message)
    update.message.message_id = 1
    update.message.reply_text = MagicMock()

    return update

@pytest.fixture
def mock_context():
    """Mock Telegram CallbackContext"""
    from unittest.mock import MagicMock
    from telegram.ext import ContextTypes

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}

    return context
```

## Unit Tests: Parsing

**File**: `test_parsers.py`

```python
from decimal import Decimal
import pytest
from telegram_bot.services.parser import parse_transaction_message

def test_parse_valid_transaction():
    result = parse_transaction_message("50/caffè al bar")
    assert result['amount'] == Decimal('50.00')
    assert result['description'] == 'caffè al bar'

def test_parse_decimal_with_dot():
    result = parse_transaction_message("125.50/spesa settimanale")
    assert result['amount'] == Decimal('125.50')
    assert result['description'] == 'spesa settimanale'

def test_parse_decimal_with_comma():
    result = parse_transaction_message("15,99/libro programmazione")
    assert result['amount'] == Decimal('15.99')

def test_parse_with_slash_in_description():
    # maxsplit=1 should handle this
    result = parse_transaction_message("50/caffè/bar")
    assert result['amount'] == Decimal('50.00')
    assert result['description'] == 'caffè/bar'

def test_parse_invalid_no_separator():
    assert parse_transaction_message("50 caffè") is None

def test_parse_invalid_no_description():
    assert parse_transaction_message("50/") is None

def test_parse_invalid_amount():
    assert parse_transaction_message("abc/caffè") is None

def test_parse_negative_amount():
    assert parse_transaction_message("-10/test") is None

def test_parse_zero_amount():
    assert parse_transaction_message("0/test") is None

def test_parse_description_too_long():
    long_desc = "x" * 201
    assert parse_transaction_message(f"50/{long_desc}") is None

def test_parse_whitespace_handling():
    result = parse_transaction_message("  50  / caffè  ")
    assert result['amount'] == Decimal('50.00')
    assert result['description'] == 'caffè'
```

## Unit Tests: Suggerimenti

**File**: `test_suggestions.py`

```python
import pytest
from django.utils import timezone
from datetime import timedelta
from telegram_bot.services.suggestions import get_subcategory_suggestions
from trantrac.models import CategoryUsage

@pytest.mark.django_db
def test_suggestions_from_user_history(user, categories_setup):
    """Le sottocategorie più usate dall'utente appaiono prime"""
    bar = categories_setup['bar']
    supermercato = categories_setup['supermercato']
    alimentari = categories_setup['alimentari']

    # Usa "Bar" 3 volte
    for _ in range(3):
        CategoryUsage.objects.create(
            user=user,
            category=alimentari,
            subcategory=bar
        )

    # Usa "Supermercato" 1 volta
    CategoryUsage.objects.create(
        user=user,
        category=alimentari,
        subcategory=supermercato
    )

    suggestions = get_subcategory_suggestions(user, "spesa")

    # "Bar" dovrebbe essere primo (più usato)
    assert suggestions[0].name == "Bar"

@pytest.mark.django_db
def test_suggestions_fuzzy_match(user, categories_setup):
    """Fuzzy match suggerisce sottocategorie simili"""
    carburante = categories_setup['carburante']

    suggestions = get_subcategory_suggestions(user, "benzina")

    # "Carburante" dovrebbe matchare con "benzina"
    assert any(s.name == "Carburante" for s in suggestions)

@pytest.mark.django_db
def test_suggestions_old_history_excluded(user, categories_setup):
    """Storico > 30 giorni non viene considerato"""
    bar = categories_setup['bar']
    alimentari = categories_setup['alimentari']

    # Crea usage 35 giorni fa
    old_usage = CategoryUsage.objects.create(
        user=user,
        category=alimentari,
        subcategory=bar
    )
    old_usage.created_at = timezone.now() - timedelta(days=35)
    old_usage.save()

    suggestions = get_subcategory_suggestions(user, "test")

    # "Bar" non dovrebbe essere suggerito (troppo vecchio)
    # (a meno che non ci sia fuzzy match)
    assert len(suggestions) <= 5

@pytest.mark.django_db
def test_suggestions_max_5(user, categories_setup):
    """Ritorna max 5 suggerimenti"""
    # Anche con molti match, max 5
    suggestions = get_subcategory_suggestions(user, "a")
    assert len(suggestions) <= 5
```

## Integration Tests: Autenticazione

**File**: `test_auth.py`

```python
import pytest
from telegram_bot.handlers.auth import handle_start, handle_contact, handle_email_message
from telegram_bot.models import TelegramAuthSession

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_start_not_authenticated(mock_update, mock_context):
    """Utente non autenticato riceve richiesta numero"""
    await handle_start(mock_update, mock_context)

    assert mock_update.message.reply_text.called
    message = mock_update.message.reply_text.call_args[0][0]
    assert "Condividi il tuo numero" in message

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_start_already_authenticated(authenticated_user, mock_update, mock_context):
    """Utente già autenticato riceve messaggio di benvenuto"""
    await handle_start(mock_update, mock_context)

    assert mock_update.message.reply_text.called
    message = mock_update.message.reply_text.call_args[0][0]
    assert "Sei già collegato" in message

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_contact_creates_session(mock_update, mock_context):
    """Condivisione numero crea sessione"""
    from unittest.mock import MagicMock
    from telegram import Contact

    mock_update.message.contact = MagicMock(spec=Contact)
    mock_update.message.contact.phone_number = "+39123456789"

    await handle_contact(mock_update, mock_context)

    # Verifica sessione creata
    assert TelegramAuthSession.objects.filter(chat_id=12345).exists()
    session = TelegramAuthSession.objects.get(chat_id=12345)
    assert session.phone_number == "+39123456789"

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_email_links_account(user, mock_update, mock_context):
    """Email corretta collega account"""
    # Crea sessione
    TelegramAuthSession.objects.create(
        chat_id=12345,
        phone_number="+39123456789"
    )

    mock_update.message.text = user.email

    await handle_email_message(mock_update, mock_context)

    # Verifica user collegato
    user.refresh_from_db()
    assert user.telegram_chat_id == 12345
    assert user.phone_number == "+39123456789"

    # Verifica sessione eliminata
    assert not TelegramAuthSession.objects.filter(chat_id=12345).exists()

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_email_not_found(mock_update, mock_context):
    """Email non trovata mostra errore"""
    TelegramAuthSession.objects.create(
        chat_id=12345,
        phone_number="+39123456789"
    )

    mock_update.message.text = "nonexist@example.com"

    await handle_email_message(mock_update, mock_context)

    assert mock_update.message.reply_text.called
    message = mock_update.message.reply_text.call_args[0][0]
    assert "Email non trovata" in message
```

## Integration Tests: Transaction Flow

**File**: `test_handlers.py`

```python
import pytest
from unittest.mock import patch
from telegram_bot.handlers.transaction import route_message
from trantrac.models import CategoryUsage

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_complete_transaction_flow(authenticated_user, categories_setup, mock_update, mock_context):
    """Test flow completo: messaggio → selezione → conferma → salvataggio"""

    with patch('telegram_bot.handlers.transaction.save_to_sheet', return_value=True):
        # Step 1: Invia transazione
        mock_update.message.text = "50/caffè al bar"
        await route_message(mock_update, mock_context)

        # Verifica lista sottocategorie mostrata
        assert mock_update.message.reply_text.called
        message1 = mock_update.message.reply_text.call_args[0][0]
        assert "50.00€" in message1
        assert "Scegli sottocategoria:" in message1

        # Step 2: Seleziona sottocategoria "1"
        mock_update.message.text = "1"
        await route_message(mock_update, mock_context)

        # Verifica conferma mostrata
        message2 = mock_update.message.reply_text.call_args[0][0]
        assert "Conferma? (s/n)" in message2

        # Step 3: Conferma
        mock_update.message.text = "s"
        await route_message(mock_update, mock_context)

        # Verifica salvato
        assert CategoryUsage.objects.filter(user=authenticated_user).exists()

        # Verifica messaggio successo
        message3 = mock_update.message.reply_text.call_args[0][0]
        assert "✅" in message3

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_transaction_cancel(authenticated_user, categories_setup, mock_update, mock_context):
    """Utente annulla transazione con 'n'"""

    # Setup pending transaction in context
    mock_context.user_data = {
        'pending_transaction': {...},
        'awaiting_confirmation': True,
    }

    mock_update.message.text = "n"
    await route_message(mock_update, mock_context)

    # Verifica annullamento
    assert "annullata" in mock_update.message.reply_text.call_args[0][0]
    assert not CategoryUsage.objects.filter(user=authenticated_user).exists()

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_transaction_sheets_failure(authenticated_user, categories_setup, mock_update, mock_context):
    """Fallimento save_to_sheet crea PendingTransaction"""
    from telegram_bot.models import PendingTransaction

    with patch('telegram_bot.handlers.transaction.save_to_sheet', side_effect=Exception("Network error")):
        # Complete flow fino a conferma
        # ... (steps come sopra) ...

        # Verifica PendingTransaction creato
        assert PendingTransaction.objects.filter(
            user=authenticated_user,
            status='pending'
        ).exists()
```

## Tests Management Commands

**File**: `test_commands.py`

```python
import pytest
from unittest.mock import patch
from django.core.management import call_command
from telegram_bot.models import PendingTransaction

@pytest.mark.django_db
def test_retry_pending_transactions_success(authenticated_user, categories_setup):
    """Retry command salva transazioni pending"""
    # Crea pending transaction
    pending = PendingTransaction.objects.create(
        user=authenticated_user,
        amount=50,
        description="test",
        category=categories_setup['alimentari'],
        subcategory=categories_setup['bar'],
        account=categories_setup['account'],
        date=timezone.now().date(),
        telegram_message_id=1,
        status='pending'
    )

    with patch('trantrac.utils.save_to_sheet', return_value=True):
        call_command('retry_pending_transactions')

    # Verifica status cambiato
    pending.refresh_from_db()
    assert pending.status == 'completed'

@pytest.mark.django_db
def test_cleanup_auth_sessions():
    """Cleanup rimuove sessioni scadute"""
    from telegram_bot.models import TelegramAuthSession
    from django.utils import timezone
    from datetime import timedelta

    # Crea sessione scaduta
    old_session = TelegramAuthSession.objects.create(
        chat_id=12345,
        phone_number="+39123"
    )
    old_session.created_at = timezone.now() - timedelta(minutes=10)
    old_session.save()

    # Crea sessione recente
    new_session = TelegramAuthSession.objects.create(
        chat_id=67890,
        phone_number="+39456"
    )

    call_command('cleanup_auth_sessions')

    # Verifica solo old eliminata
    assert not TelegramAuthSession.objects.filter(chat_id=12345).exists()
    assert TelegramAuthSession.objects.filter(chat_id=67890).exists()
```

## Running Tests

```bash
# All tests
pytest telegram_bot/tests/

# Specific file
pytest telegram_bot/tests/test_parsers.py

# Specific test
pytest telegram_bot/tests/test_parsers.py::test_parse_valid_transaction

# With coverage
pytest telegram_bot/tests/ --cov=telegram_bot --cov-report=html

# Fast parallel
pytest telegram_bot/tests/ -n 8
```

## Coverage Goals

- **Unit tests**: > 90%
- **Integration tests**: > 80%
- **Overall**: > 85%

## Manual Testing Checklist

Vedi `.beans/00-checklist.md`
