---
# trantrac-ev7w
title: 'Bot Telegram: visualizza e cancella ultime transazioni'
status: todo
type: feature
priority: normal
created_at: 2026-02-13T07:43:14Z
updated_at: 2026-02-13T08:10:30Z
---

Aggiungere al bot Telegram la possibilità di:
1. Visualizzare le ultime 5 transazioni inserite tramite bot con /ultimi
2. Cancellare una transazione dalla lista (da DB locale + Google Sheets)

## Contesto
- Le transazioni attuali vengono salvate SOLO su Google Sheets, senza tracciamento locale
- Non esiste un modello Transaction locale, solo PendingTransaction (per i falliti)
- Il bot usa python-telegram-bot (PTB) con handler asincroni

## Approccio
1. Creare modello BotTransaction per tracciare le transazioni salvate con successo via bot
2. Modificare create_transaction() per salvare nel nuovo modello
3. Aggiungere comando /ultimi con lista numerata delle ultime 5
4. Implementare cancellazione con InlineKeyboardMarkup (callback buttons) o selezione numerata
5. La cancellazione deve rimuovere da DB locale; la rimozione da Sheets è opzionale/best-effort

## Issue\nCodeberg #54
