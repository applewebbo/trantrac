---
# trantrac-bdmf
title: Aggiungere helper di autenticazione per il bot
status: todo
type: task
priority: normal
created_at: 2026-02-19T14:02:52Z
updated_at: 2026-02-19T14:03:44Z
parent: trantrac-sy3t
blocked_by:
    - trantrac-lbe9
---

## Descrizione

Creare un modulo `telegram_bot/utils/auth.py` con helper per verificare lo stato dell'utente in tutti gli handler del bot.

## Dettagli Tecnici

**Nuovo file**: `telegram_bot/utils/auth.py`

```python
async def get_approved_user(update) -> User | None:
    """Ritorna l'utente se autenticato e approvato, altrimenti None."""
    chat_id = update.effective_chat.id
    try:
        user = await sync_to_async(User.objects.get)(
            telegram_chat_id=chat_id,
            telegram_status=User.TELEGRAM_STATUS_APPROVED,
        )
        return user
    except User.DoesNotExist:
        return None

async def get_pending_user(update) -> User | None:
    """Ritorna l'utente se in stato pending."""
    ...

async def reply_if_not_enrolled(update) -> bool:
    """Invia messaggio appropriato se non autenticato/pending. Ritorna True se deve uscire dall'handler."""
    chat_id = update.effective_chat.id
    # Check: non esiste → 'Usa /start per collegarti'
    # Check: pending → 'In attesa di approvazione admin'
    # Check: approved → continua
```

## Tasks
- [ ] Creare `telegram_bot/utils/__init__.py`
- [ ] Creare `telegram_bot/utils/auth.py` con `get_approved_user`, `get_pending_user`, `reply_if_not_enrolled`
- [ ] Scrivere test per gli helper
