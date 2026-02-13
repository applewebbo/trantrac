---
# trantrac-zgat
title: Creare modello BotTransaction per tracciare transazioni salvate via bot
status: completed
type: task
priority: normal
created_at: 2026-02-13T07:43:21Z
updated_at: 2026-02-13T08:15:00Z
parent: trantrac-ev7w
---

Creare il modello Django BotTransaction in telegram_bot/models.py per tracciare le transazioni salvate con successo via bot.

## Campi necessari
- user: ForeignKey(User)
- amount: DecimalField
- description: CharField
- category: ForeignKey(Category)
- subcategory: ForeignKey(Subcategory)
- account: ForeignKey(Account)
- date: DateField
- created_at: DateTimeField(auto_now_add=True)
- telegram_message_id: BigIntegerField
- bot_id: CharField(max_length=20, unique=True) — identificativo univoco formato BOT-XXXXXXXX (es. BOT-A3F2C9E1)

## Task
- [x] Aggiungere modello BotTransaction a telegram_bot/models.py
- [x] Creare migrazione con makemigrations
- [x] Modificare create_transaction() in transaction_service.py per salvare BotTransaction su successo
- [x] Scrivere test per il modello e la modifica al service

## Note
- bot_id viene generato al momento del salvataggio: uuid4().hex[:8].upper() prefissato da 'BOT-'
- Il bot ora salva 8 colonne su USCITE (aggiunta la colonna 'Codice identificativo' = bot_id)
- Dopo ogni salvataggio riuscito, eliminare automaticamente le BotTransaction dell'utente oltre le prime 5 (ordered by -created_at)
- La colonna 'Codice identificativo' è già usata dall'import CSV: il bot la popola con BOT-XXXXXXXX
- Aggiungere a admin.py per visibilità

## Summary of Changes
- Aggiunto modello BotTransaction con bot_id (BOT-XXXXXXXX), migrazione 0002_bottransaction
- generate_bot_id() usa uuid4().hex[:8].upper() prefissato BOT-
- create_transaction() ora salva 8 colonne su USCITE (aggiunta Codice identificativo = bot_id)
- BotTransaction salvato su successo; _prune_bot_transactions() mantiene max 5 per utente
- Admin registrato; 13 nuovi test, coverage 100%
