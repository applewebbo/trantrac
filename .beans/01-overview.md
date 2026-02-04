# Overview: Telegram Bot per TranTrac

## Obiettivo

Implementare un bot Telegram che permetta agli utenti di inserire transazioni (solo USCITE/spese) tramite messaggi, con sincronizzazione automatica a Google Sheets.

## Decisioni di Design

### Formato Messaggio
**Scelta**: `IMPORTO/DESCRIZIONE` (es: `50/caffè al bar`)

**Rationale**:
- Semplice da ricordare e digitare
- Solo 2 campi richiesti dall'utente
- Bot suggerisce intelligentemente le sottocategorie

**Alternative scartate**:
- `IMPORTO/DESCRIZIONE/SOTTOCATEGORIA` - troppo da digitare
- Natural Language Processing - overhead eccessivo
- Conversazione guidata multi-step - troppo verboso

### Selezione Sottocategoria
**Scelta**: Elenco numerato (top 5) + opzione "0. Altro..."

**Rationale**:
- Più user-friendly su mobile
- No errori di digitazione
- Suggerimenti intelligenti basati su storico + fuzzy match

**Flusso**:
1. Bot mostra top 5 sottocategorie suggerite
2. Utente risponde con numero (1-5)
3. Se utente sceglie "0", mostra tutte le sottocategorie (paginate, 10 per pagina)
4. Conferma finale con "s/n"

### Autenticazione
**Scelta**: Numero di telefono (via Telegram) + Email

**Rationale**:
- Nessuna pagina web necessaria
- Numero verificato direttamente da Telegram
- Email collega a User esistente

**Flusso**:
1. `/start` → Bot chiede numero (bottone Telegram)
2. Utente condivide numero
3. Bot chiede email
4. Sistema cerca User con quella email
5. Se trovato: salva phone_number e telegram_chat_id

**Sicurezza**:
- "Primo che arriva vince" (adatto per uso familiare)
- Sessione temporanea (5 minuti TTL)
- Possibilità futura di aggiungere verifica SMS

### Deployment
**Scelta**: Webhook (produzione) + Polling (dev)

**Rationale**:
- Webhook è best practice per produzione
- Polling comodo per dev/test (no endpoint pubblico necessario)
- python-telegram-bot supporta entrambi

### Async Strategy
**Scelta**: Handlers async nativi (no Celery)

**Rationale**:
- python-telegram-bot già async
- `save_to_sheet()` è veloce (<500ms)
- PendingTransaction gestisce fallimenti
- Celery aggiunge overhead non necessario

## Requisiti Confermati

- ✅ Solo USCITE (no entrate)
- ✅ Data sempre corrente (no selezione data)
- ✅ Formato: IMPORTO/DESCRIZIONE
- ✅ Selezione numerica sottocategoria
- ✅ Suggerimenti: storico utente + fuzzy match
- ✅ Fallback: "0. Altro..." con paginazione
- ✅ Solo inserimento transazioni (no comandi stats)
- ✅ Auth: numero di telefono + email

## Stack Tecnico

- **Backend**: Django 5.1 + Python 3.13+
- **Bot Library**: python-telegram-bot v21+ (async)
- **Database**: SQLite (esistente)
- **Google Sheets**: API esistente (riutilizzata)
- **Deployment**: Webhook HTTPS

## Architettura App

```
telegram_bot/
├── models.py              # PendingTransaction, TelegramAuthSession
├── handlers/
│   ├── auth.py            # Autenticazione
│   └── transaction.py     # Transazioni
├── services/
│   ├── parser.py          # Parsing messaggi
│   └── suggestions.py     # Suggerimenti intelligenti
├── management/commands/   # Bot runner, webhook setup, retry
└── tests/                 # Unit + integration tests
```

## Integrazione con Codice Esistente

### Riutilizzo

- `trantrac/utils.py:save_to_sheet()` - salvataggio su Sheets (identica)
- Pattern `views.py:43-73` - creazione transazione
- Modelli: Category, Subcategory, Account, CategoryUsage

### Modifiche

- `users/models.py` - +2 campi: telegram_chat_id, phone_number
- `core/settings.py` - +INSTALLED_APPS, env vars Telegram
- `core/urls.py` - include telegram_bot.urls

## Metriche di Successo

- Latenza messaggio → risposta: **< 2 secondi**
- Success rate save_to_sheet: **> 99%**
- Retry pending transactions: **100% entro 1 ora**
- Zero falsi positivi rate limiting

## Rischi e Mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---------|-------------|---------|-------------|
| Google Sheets quota limit | Media | Alto | PendingTransaction + retry automatico |
| Autenticazione non sicura | Bassa | Medio | Uso familiare, possibile aggiungere SMS |
| Spam bot | Bassa | Medio | Rate limiting + auth obbligatoria |
| Telegram webhook down | Molto bassa | Medio | Telegram retry automatici |

## Future Enhancements (Out of Scope)

- Supporto ENTRATE
- Comandi /stats, /last
- Data personalizzata
- Modifica transazione
- Notifiche proattive
- Voice/photo parsing
