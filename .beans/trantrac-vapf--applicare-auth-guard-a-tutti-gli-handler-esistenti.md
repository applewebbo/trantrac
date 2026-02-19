---
# trantrac-vapf
title: Applicare auth guard a tutti gli handler esistenti del bot
status: todo
type: task
priority: normal
created_at: 2026-02-19T14:03:21Z
updated_at: 2026-02-19T14:03:54Z
parent: trantrac-sy3t
blocked_by:
    - trantrac-bdmf
    - trantrac-zw4y
---

## Descrizione

Aggiornare tutti gli handler esistenti del bot per usare i nuovi helper di autenticazione, in modo che solo utenti con `telegram_status='approved'` possano eseguire azioni.

## Handler da Aggiornare

### `telegram_bot/handlers/transaction.py`
- `route_message`: sostituire lookup utente con `get_approved_user` + early return se non approvato

### `telegram_bot/handlers/history.py`
- `handle_recent_transactions`: idem

### `telegram_bot/handlers/auth.py`
- `handle_start`: aggiornare messaggio benvenuto basandosi su is_staff (mostrare comandi diversi)

## Comportamento per Stato

| Stato | Risposta bot |
|-------|-------------|
| Non registrato | 'Usa /start per collegare il tuo account' |
| Pending | '⏳ Richiesta in attesa di approvazione. Ti notificherò appena confermata.' |
| Approved | Continua normalmente |

## Messaggio /start per utenti approvati

- **Admin**: mostrare comandi extra (`/csv`, future funzionalità admin)
- **Utente normale**: solo comandi standard (`/ultime`)

## Tasks
- [ ] Aggiornare `route_message` in transaction.py
- [ ] Aggiornare `handle_recent_transactions` in history.py
- [ ] Aggiornare messaggio /start benvenuto per admin vs utente normale
- [ ] Scrivere test per i vari casi
