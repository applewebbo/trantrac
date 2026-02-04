# Checklist Implementazione Telegram Bot

**Issue**: #35 (Codeberg)

## Setup Iniziale

- [ ] Crea bot con BotFather
  - [ ] `/newbot` → nome: "TranTrac Bot"
  - [ ] Copia `TELEGRAM_BOT_TOKEN`
  - [ ] `/setcommands`: start, help
- [ ] Aggiungi dependency: `uv add python-telegram-bot[webhook]`
- [ ] Aggiungi variabili a `.env.example`

## Modifiche Database

- [ ] Aggiungi campi a `users/models.py`:
  - [ ] `telegram_chat_id` (BigIntegerField, unique)
  - [ ] `phone_number` (CharField, max_length=20)
- [ ] Crea app `telegram_bot/`
- [ ] Crea modelli:
  - [ ] `PendingTransaction`
  - [ ] `TelegramAuthSession`
  - [ ] `CategoryKeyword` (opzionale)
- [ ] Run migrations: `python manage.py makemigrations` + `migrate`

## Configurazione Django

- [ ] Aggiungi `telegram_bot` a `INSTALLED_APPS` in `settings.py`
- [ ] Aggiungi env vars in `settings.py`:
  - [ ] `TELEGRAM_BOT_TOKEN`
  - [ ] `TELEGRAM_WEBHOOK_URL`
  - [ ] `TELEGRAM_WEBHOOK_SECRET`
  - [ ] `SITE_URL`
- [ ] Include `telegram_bot.urls` in `core/urls.py`

## Implementazione Handlers

### Autenticazione
- [ ] `handlers/auth.py`:
  - [ ] `handle_start()` - comando /start con bottone condividi numero
  - [ ] `handle_contact()` - riceve numero di telefono
  - [ ] `handle_email_message()` - riceve email e collega account

### Transazioni
- [ ] `handlers/transaction.py`:
  - [ ] `route_message()` - router principale messaggi
  - [ ] `handle_transaction_message()` - parsing IMPORTO/DESCRIZIONE
  - [ ] `send_subcategory_list()` - mostra elenco numerato top 5
  - [ ] `handle_subcategory_selection()` - gestisce scelta numero
  - [ ] `show_all_subcategories()` - mostra tutte (paginate)
  - [ ] `handle_navigation()` - paginazione con n/p
  - [ ] `handle_final_confirmation()` - conferma s/n
  - [ ] `create_and_save_transaction()` - salva su Sheets

## Implementazione Services

- [ ] `services/parser.py`:
  - [ ] `parse_transaction_message()` - parsing IMPORTO/DESCRIZIONE
- [ ] `services/suggestions.py`:
  - [ ] `get_subcategory_suggestions()` - storico + fuzzy match
- [ ] `services/transaction_service.py`:
  - [ ] Business logic transazioni

## Views e URLs

- [ ] `views.py`:
  - [ ] `telegram_webhook()` - riceve updates Telegram
- [ ] `urls.py`:
  - [ ] Route `/webhook/`

## Management Commands

- [ ] `management/commands/runbot.py` - polling mode per dev
- [ ] `management/commands/setwebhook.py` - configura webhook produzione
- [ ] `management/commands/retry_pending_transactions.py` - retry falliti
- [ ] `management/commands/cleanup_auth_sessions.py` - pulisci sessioni scadute

## Testing

### Unit Tests
- [ ] `tests/test_parsers.py`:
  - [ ] test_parse_valid_transaction
  - [ ] test_parse_decimal_transaction
  - [ ] test_parse_comma_decimal
  - [ ] test_parse_invalid_format
- [ ] `tests/test_suggestions.py`:
  - [ ] test_suggestions_from_user_history
  - [ ] test_suggestions_fuzzy_match

### Integration Tests
- [ ] `tests/test_handlers.py`:
  - [ ] test_transaction_flow_complete
  - [ ] test_auth_flow
  - [ ] test_pagination

### Manual Testing
- [ ] /start → condividi numero → email → collegamento
- [ ] Invia "50/caffè" → lista suggerimenti
- [ ] Seleziona "1" → conferma
- [ ] Conferma "s" → verifica su Sheets
- [ ] Test "0. Altro..." → paginazione
- [ ] Test annullamento con "n"
- [ ] Test Google Sheets offline → PendingTransaction
- [ ] Test retry command

## Deployment

### Development
- [ ] Setup `.env` per polling mode
- [ ] Run: `python manage.py runbot`
- [ ] Test completo flusso

### Production
- [ ] Setup `.env` per webhook mode
- [ ] Deploy codice
- [ ] Run migrations
- [ ] Setup webhook: `python manage.py setwebhook`
- [ ] Verifica: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`

### Cronjobs
- [ ] Aggiungi retry_pending_transactions (ogni 15 min)
- [ ] Aggiungi cleanup_auth_sessions (ogni ora)

## Verifica Finale

- [ ] Test end-to-end completo in produzione
- [ ] Verifica metriche:
  - [ ] Latenza < 2 secondi
  - [ ] Success rate > 99%
  - [ ] Retry entro 1 ora
- [ ] Monitoring attivo
- [ ] Documentation aggiornata
