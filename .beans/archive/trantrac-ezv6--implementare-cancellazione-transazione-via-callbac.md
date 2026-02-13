---
# trantrac-ezv6
title: Implementare cancellazione transazione via callback inline button
status: completed
type: task
priority: normal
created_at: 2026-02-13T07:43:40Z
updated_at: 2026-02-13T08:27:23Z
parent: trantrac-ev7w
blocked_by:
    - trantrac-t20w
---

Gestire il callback 'delete:<id>' dei bottoni inline per cancellare una BotTransaction.

## Comportamento
1. Utente preme 'Elimina' su una transazione dalla lista /ultimi
2. Bot chiede conferma: 'Sei sicuro di voler eliminare: 50€ - caffè al bar? (s/n)'
   oppure con bottoni inline Sì/No
3. Su conferma:
   - Elimina BotTransaction dal DB
   - Tenta di rimuovere la riga da Google Sheets (best-effort: se fallisce, logga ma non blocca)
   - Risponde con conferma ✅
4. Su annullamento: messaggio di annullamento

## Strategia cancellazione da Google Sheets
- Cerca la riga in USCITE dove la colonna 'Codice identificativo' (colonna H) == bot_id
- Usa get_sheet_data() per recuperare tutti i valori di USCITE!H:H, trova il match, poi batchUpdate/deleteRange su quella riga
- Obbligatoria: se la cancellazione da Sheets fallisce → l'operazione fallisce intera, il record DB NON viene eliminato
- Risponde con errore all'utente se Sheets non è raggiungibile o la riga non viene trovata

## Task
- [x] Creare handler handle_delete_callback() per CallbackQueryHandler
- [x] Implementare delete_bot_transaction() in transaction_service.py e delete_row_by_identifier() in utils.py
- [x] Registrare CallbackQueryHandler in runbot.py e views.py (+ callback_query in allowed_updates + setwebhook)
- [x] Gestire conferma via bottoni inline Sì/No (confirm_delete/cancel_delete)
- [x] Scrivere test per handler, service e utils

## Note
- Usare answer_callback_query() per rimuovere lo spinner dal bottone
- Proteggere: verificare che l'utente che cancella sia lo stesso che ha creato la transazione

## Summary of Changes
- Nuovo handler handle_delete_callback() in history.py: delete → confirm_delete/cancel_delete
- delete_bot_transaction() in transaction_service.py: atomico (Sheets prima, DB dopo)
- delete_row_by_identifier() in utils.py: cerca per BOT-ID in colonna H, poi batchUpdate deleteRange
- CallbackQueryHandler registrato in runbot.py, views.py, setwebhook.py (+ callback_query negli allowed_updates)
- 335 test totali, coverage 100%
