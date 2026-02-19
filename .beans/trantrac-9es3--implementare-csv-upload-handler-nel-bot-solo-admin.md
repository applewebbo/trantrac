---
# trantrac-9es3
title: Implementare CSV upload handler nel bot (solo admin)
status: completed
type: task
priority: normal
created_at: 2026-02-19T14:03:34Z
updated_at: 2026-02-19T14:29:08Z
parent: trantrac-sy3t
blocked_by:
    - trantrac-vapf
---

## Descrizione

Aggiungere la possibilità di caricare un file CSV direttamente dal bot Telegram. Funzionalità riservata agli admin (is_staff).

## Flusso

```
Admin invia file .csv al bot
    ↓
Bot verifica: admin? → No → '❌ Funzione riservata agli admin.'
    ↓ Sì
Bot verifica: estensione .csv? → No → '❌ Invia un file .csv valido.'
    ↓ Sì
Bot: '⏳ Elaborazione CSV in corso...'
    ↓
Download file da Telegram in memoria (BytesIO)
    ↓
import_csv_to_sheet(file_like, user)
    ↓
Successo: '✅ CSV importato: N transazioni (X entrate, Y uscite)'
Errore:   '❌ Errore nell'importazione: [messaggio errore]'
```

## Dettagli Tecnici

**Nuovo file**: `telegram_bot/handlers/csv_upload.py`

- Handler: `MessageHandler(filters.Document.FileExtension('csv'), handle_csv_upload)`
- Download: `file = await context.bot.get_file(document.file_id)` + `download_to_memory()` → `io.BytesIO`
- Riutilizza `import_csv_to_sheet` da `trantrac.utils`
- La funzione esistente usa `csv_file.read().decode('utf-8-sig')`, quindi BytesIO è compatibile

## Aggiornamenti al Bot

- Registrare handler in `runbot.py` e `views.py`
- Aggiungere comando `/csv` nella lista BotCommand (solo visibile agli admin via `setwebhook`)
- Aggiungere istruzioni nel messaggio /start per admin

## Tasks
- [x] Creare `telegram_bot/handlers/csv_upload.py` con `handle_csv_upload`
- [ ] Registrare handler in runbot.py e views.py
- [ ] Aggiungere `/csv` ai BotCommand
- [ ] Scrivere test
