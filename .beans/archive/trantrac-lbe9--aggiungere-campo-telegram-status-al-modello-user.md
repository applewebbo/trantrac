---
# trantrac-lbe9
title: Aggiungere campo telegram_status al modello User
status: completed
type: task
priority: normal
created_at: 2026-02-19T14:02:43Z
updated_at: 2026-02-19T14:09:43Z
parent: trantrac-sy3t
---

## Descrizione

Aggiungere il campo `telegram_status` al modello `users.User` per tracciare lo stato di approvazione dell'enrollment Telegram.

## Dettagli Tecnici

**File**: `users/models.py`

Aggiungere al modello User:
```python
TELEGRAM_STATUS_PENDING = 'pending'
TELEGRAM_STATUS_APPROVED = 'approved'
TELEGRAM_STATUS_CHOICES = [
    ('pending', 'In attesa di approvazione'),
    ('approved', 'Approvato'),
]
telegram_status = models.CharField(
    max_length=20,
    choices=TELEGRAM_STATUS_CHOICES,
    null=True,
    blank=True,
    help_text='Stato approvazione enrollment Telegram',
)
```

- `NULL` = utente non ha mai iniziato enrollment
- `'pending'` = enrollment completato, in attesa di approvazione admin
- `'approved'` = utente approvato, può usare il bot

## Tasks
- [x] Aggiungere campo `telegram_status` al modello User
- [ ] Creare migration
- [ ] Aggiornare admin Django per visualizzare/modificare il campo
- [ ] Aggiornare test modello User se esistenti
