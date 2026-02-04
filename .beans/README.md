# Telegram Bot Implementation Beans

**Issue**: #35 (Codeberg)

Questa directory contiene la documentazione organizzata per l'implementazione del Telegram Bot per TranTrac.

## Struttura Beans

Ogni "bean" è un file markdown che copre un aspetto specifico dell'implementazione:

### 00-checklist.md
Checklist completa di tutti i task da completare per l'implementazione. Usala per tracciare il progresso.

**Quando usarla**: Durante tutta l'implementazione, spunta i task man mano che vengono completati.

### 01-overview.md
Panoramica del progetto: decisioni di design, requisiti confermati, stack tecnico, architettura generale.

**Quando usarla**: Prima di iniziare l'implementazione, per capire il quadro generale e le scelte fatte.

### 02-authentication.md
Flow di autenticazione completo: numero di telefono + email, modelli necessari, gestione errori.

**Quando usarla**: Quando implementi il sistema di autenticazione (primo step).

### 03-models.md
Tutti i modelli Django da creare: PendingTransaction, TelegramAuthSession, CategoryKeyword, con esempi di uso e admin.

**Quando usarla**: Quando crei/modifichi i modelli Django e le migrations.

### 04-transaction-flow.md
Flow completo delle transazioni: parsing, suggerimenti, selezione sottocategoria, conferma, salvataggio.

**Quando usarla**: Quando implementi i handlers delle transazioni (core del bot).

### 05-google-sheets.md
Integrazione con Google Sheets: riutilizzo codice esistente, formato dati, gestione fallimenti, retry.

**Quando usarla**: Quando implementi il salvataggio su Sheets e il sistema di retry.

### 06-deployment.md
Setup completo: BotFather, environment variables, webhook, polling mode, cronjobs, monitoring.

**Quando usarla**: Durante il deployment in development e production.

### 07-testing.md
Strategy di testing completa: unit tests, integration tests, fixtures, manual testing.

**Quando usarla**: Quando scrivi i test (fallo durante l'implementazione, non alla fine!).

## Come Usare i Beans

### Approccio Consigliato

1. **Leggi** `01-overview.md` per capire il quadro generale
2. **Segui** `00-checklist.md` come guida step-by-step
3. **Consulta** gli altri beans quando implementi quella specifica parte

### Flusso di Implementazione Suggerito

```
1. Setup & Models
   → Leggi: 03-models.md
   → Implementa: modelli + migrations
   → Test: unit tests sui modelli

2. Autenticazione
   → Leggi: 02-authentication.md
   → Implementa: handlers auth
   → Test: test_auth.py

3. Transazioni
   → Leggi: 04-transaction-flow.md
   → Implementa: handlers transaction
   → Test: test_handlers.py

4. Google Sheets
   → Leggi: 05-google-sheets.md
   → Implementa: integrazione + retry
   → Test: mock save_to_sheet

5. Deployment
   → Leggi: 06-deployment.md
   → Setup: webhook/polling
   → Test: manual testing checklist

6. Testing Finale
   → Leggi: 07-testing.md
   → Completa: coverage report
   → Verifica: tutti i test passano
```

## Quick Reference

### File Critici da Modificare
- `users/models.py` - +telegram_chat_id, +phone_number
- `core/settings.py` - +INSTALLED_APPS, +env vars
- `core/urls.py` - include telegram_bot.urls

### File Critici da Riutilizzare
- `trantrac/utils.py:save_to_sheet()` - salvataggio Sheets
- `trantrac/views.py:43-73` - pattern creazione transazione
- `trantrac/models.py` - Category, Subcategory, Account, CategoryUsage

### Commands Utili

```bash
# Development
python manage.py runbot

# Migrations
python manage.py makemigrations users telegram_bot
python manage.py migrate

# Testing
pytest telegram_bot/tests/
pytest --cov=telegram_bot

# Deployment
python manage.py setwebhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# Management
python manage.py retry_pending_transactions
python manage.py cleanup_auth_sessions
```

## Link al Piano Completo

Il piano completo originale è in:
`/Users/enricobonardi/.claude/plans/proud-wobbling-moore.md`

I beans sono estratti organizzati da quel piano per facilitare l'implementazione.

## Aggiornamenti

Quando apporti modifiche durante l'implementazione:
- ✅ Aggiorna il bean corrispondente
- ✅ Spunta la checklist (00-checklist.md)
- ✅ Documenta decisioni importanti nel bean appropriato

## Domande?

Se hai dubbi durante l'implementazione, consulta prima il bean corrispondente. Se la risposta non c'è, può essere un'ottima occasione per aggiornare la documentazione!
