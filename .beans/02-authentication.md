# Autenticazione Telegram Bot

## Flow Completo

```
┌─────────────┐
│ Utente      │
│ invia       │
│ /start      │
└──────┬──────┘
       │
       v
┌─────────────────────────────┐
│ Bot: "Condividi numero"     │
│ [📱 Condividi il tuo numero]│ <- KeyboardButton
└──────┬──────────────────────┘
       │
       v
┌──────────────────────────┐
│ Utente condivide numero  │
│ (via Telegram nativo)    │
└──────┬───────────────────┘
       │
       v
┌───────────────────────────────────┐
│ Bot salva in TelegramAuthSession  │
│ (chat_id, phone_number)           │
└──────┬────────────────────────────┘
       │
       v
┌────────────────────────────┐
│ Bot: "Inviami la tua email"│
└──────┬─────────────────────┘
       │
       v
┌──────────────────────┐
│ Utente invia email   │
│ es: enrico@email.com │
└──────┬───────────────┘
       │
       v
┌────────────────────────────────┐
│ Sistema cerca User by email    │
└──────┬─────────────────────────┘
       │
       ├─ Trovato ──> Salva telegram_chat_id + phone_number
       │              Elimina TelegramAuthSession
       │              "✅ Account collegato!"
       │
       └─ Non trovato ──> "❌ Email non trovata. Registrati su [URL]"
                          Elimina TelegramAuthSession
```

## Modello TelegramAuthSession

**File**: `telegram_bot/models.py`

```python
from django.db import models
from django.utils import timezone
from datetime import timedelta

class TelegramAuthSession(models.Model):
    """Sessione temporanea per autenticazione via numero telefono"""

    chat_id = models.BigIntegerField(unique=True)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['chat_id'])]

    def is_expired(self):
        """Sessione scade dopo 5 minuti"""
        return timezone.now() > self.created_at + timedelta(minutes=5)
```

## Modifiche User Model

**File**: `users/models.py`

```python
class User(AbstractUser):
    # ... existing fields ...

    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID chat Telegram per bot"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Numero di telefono per autenticazione Telegram"
    )
```

**Migration**:
```bash
python manage.py makemigrations users --name add_telegram_fields
python manage.py migrate users
```

## Gestione Errori

### Email non trovata
```
❌ Email non trovata.

Registrati prima su: https://trantrac.com
```

### Sessione scaduta
```
❌ Sessione scaduta. Invia /start per ricominciare.
```

### Email formato invalido
```
❌ Email non valida. Riprova.
```

## Management Command: Cleanup

**Cronjob**:
```bash
# Ogni ora
0 * * * * cd /path/to/trantrac && python manage.py cleanup_auth_sessions
```
