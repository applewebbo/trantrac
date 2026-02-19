---
# trantrac-zw4y
title: Aggiornare enrollment flow con approvazione admin
status: todo
type: task
priority: normal
created_at: 2026-02-19T14:03:09Z
updated_at: 2026-02-19T14:03:44Z
parent: trantrac-sy3t
blocked_by:
    - trantrac-lbe9
---

## Descrizione

Modificare il flusso di enrollment in `telegram_bot/handlers/auth.py` per implementare l'approvazione admin.

## Nuovo Flusso

```
/start → condividi telefono → inserisci email
    ↓
Email trovata nel DB?
    ↓ Sì
is_staff == True?
    ├── Sì → telegram_status = 'approved', salva, messaggio 'Benvenuto admin\!'
    └── No  → telegram_status = 'pending', salva
                ↓
                Notifica TUTTI gli admin con telegram_chat_id approvato:
                '🔐 Nuova richiesta da [nome/email]
                 [✅ Approva] [❌ Rifiuta]'
                ↓
                Utente: 'Richiesta inviata, attendi approvazione admin'
```

## Admin Approval Callback

Nuovo callback handler pattern: `^(approve_enrollment:|reject_enrollment:)`

```
approve_enrollment:{user_id}
    → User.telegram_status = 'approved'
    → Notifica utente: '✅ Approvato\! Puoi usare il bot.'
    → Aggiorna messaggio admin: '✅ Approvato [nome]'

reject_enrollment:{user_id}
    → User.telegram_chat_id = None, telegram_status = None
    → Notifica utente: '❌ Richiesta rifiutata. Contatta l'admin.'
    → Aggiorna messaggio admin: '❌ Rifiutato [nome]'
```

## Edge Cases

- Email non trovata: messaggio errore invariato
- Nessun admin con Telegram attivo: messaggio all'utente 'Nessun admin disponibile, contatta manualmente'
- Admin già linked si ri-enrolla: se già approved, messaggio 'Già collegato'
- User pending che ri-invia email: non creare duplicati, rimandare notifica o messaggio 'Già in attesa'

## Files da Modificare
- `telegram_bot/handlers/auth.py`: `handle_email_message`, aggiungere `handle_enrollment_approval`
- `telegram_bot/management/commands/runbot.py`: registrare nuovo callback handler
- `telegram_bot/views.py`: registrare nuovo callback handler nel webhook

## Tasks
- [ ] Modificare `handle_email_message` per differenziare staff da utenti normali
- [ ] Aggiungere funzione `_notify_admins_of_enrollment(context, user)`
- [ ] Creare `handle_enrollment_approval` callback handler (approve/reject)
- [ ] Registrare callback handler in runbot.py e views.py
- [ ] Gestire tutti gli edge cases
- [ ] Scrivere test
