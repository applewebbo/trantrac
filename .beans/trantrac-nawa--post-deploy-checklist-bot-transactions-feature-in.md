---
# trantrac-nawa
title: 'Post-deploy checklist: bot transactions feature in production'
status: todo
type: task
priority: normal
created_at: 2026-02-13T08:43:01Z
updated_at: 2026-02-13T08:49:30Z
---

Checklist delle operazioni da eseguire dopo il deploy del branch 2026.4 in produzione per testare il bot.

## 1. Variabili d'ambiente (già presenti in .env prod)
- [ ] Verificare che `TELEGRAM_BOT_TOKEN` sia valorizzato
- [ ] Verificare che `TELEGRAM_WEBHOOK_URL` punti al dominio di produzione (es. `https://trantrac.example.com`)
- [ ] Verificare che `TELEGRAM_WEBHOOK_SECRET` sia valorizzato

## 2. Migrazione DB (automatica con entrypoint.sh)
- [ ] Confermare che la migrazione `telegram_bot.0002_bottransaction` sia applicata
  - entrypoint.sh esegue già `python manage.py migrate` → automatico

## 3. Re-registrazione webhook (manuale, una tantum)
Dopo il deploy, eseguire dalla shell del container (o Caprover console):
```
python manage.py setwebhook
```
Questo aggiornerà:
- [ ] `allowed_updates` con `callback_query` (necessario per i bottoni inline delete)
- [ ] `set_my_commands` con `/start` e `/ultime` nel menu del bot

## 4. Google Sheets — aggiungere header colonna H su USCITE (manuale)
Il foglio USCITE ora riceve un 8° valore (Codice identificativo = BOT-XXXXXXXX).
- [x] Header colonna H su USCITE: presente come `Identificativo` — funziona correttamente (la ricerca avviene per valore, non per header)

## 5. Test funzionali in produzione
- [ ] Inviare una transazione via bot → verificare che colonna H di USCITE contenga `XXXXXXXX-BOT`
- [ ] Inviare `/ultime` → verificare che appaia la lista con bottoni Elimina
- [ ] Premere Elimina su una transazione → verificare conferma Sì/No
- [ ] Confermare la cancellazione → verificare che la riga venga rimossa da Google Sheets e dal DB
- [ ] Verificare che `/ultime` e `/start` appaiano nel menu comandi del bot (tocca il campo di testo → icona /)

## Note
- La cancellazione è obbligatoria: se Sheets non è raggiungibile, il record DB NON viene eliminato
- Max 5 BotTransaction per utente in DB — le vecchie vengono eliminate automaticamente
