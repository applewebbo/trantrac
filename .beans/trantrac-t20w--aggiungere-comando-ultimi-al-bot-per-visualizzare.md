---
# trantrac-t20w
title: Aggiungere comando /ultimi al bot per visualizzare le ultime 5 transazioni
status: completed
type: task
priority: normal
created_at: 2026-02-13T07:43:29Z
updated_at: 2026-02-13T08:21:29Z
parent: trantrac-ev7w
blocked_by:
    - trantrac-zgat
---

Implementare il comando /ultimi in telegram_bot/handlers/transaction.py (o nuovo file history.py).

## Comportamento
- Risponde al comando /ultimi
- Mostra le ultime 5 BotTransaction dell'utente autenticato
- Formato: lista numerata con data, importo, descrizione, categoria>sottocategoria
- Se non ci sono transazioni, messaggio informativo
- Ogni voce ha un bottone inline 'Elimina' (InlineKeyboardMarkup)

## Esempio output
```
📋 Ultime 5 transazioni:

1. 13/02/2026 — 50€ — caffè al bar
   📊 Alimentari > Bar
2. 12/02/2026 — 120€ — benzina
   📊 Trasporti > Carburante
...

Seleziona il numero da cancellare, oppure /annulla
```

## Task
- [x] Creare handler handle_recent_transactions() per il comando /ultimi
- [x] Registrare CommandHandler('ultimi', ...) in runbot.py e views.py (webhook)
- [x] Usare InlineKeyboardMarkup con callback_data='delete:<bot_id>' per ogni transazione
- [x] Scrivere test per l'handler (pytest-asyncio con asyncio_mode=auto)

## Summary of Changes
- Nuovo file telegram_bot/handlers/history.py con handle_recent_transactions()
- Registrato CommandHandler('ultimi') in runbot.py e views.py
- InlineKeyboardButton con callback_data='delete:BOT-XXXXXXXX' per ogni transazione
- Aggiunto pytest-asyncio, asyncio_mode=auto in pyproject.toml
- 5 test asincroni, coverage 100%
