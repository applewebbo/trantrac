# Integrazione Google Sheets

## Riutilizzo Codice Esistente

Il bot riutilizza completamente la funzione esistente `save_to_sheet()` da `trantrac/utils.py`.

**Riferimento**: `/Users/enricobonardi/CODING/WEBBO_PROJECTS/trantrac/trantrac/utils.py:155-175`

## Formato Dati

### USCITE (Spese)

```python
values = [[
    str(user.display_name),                          # Col A: Nome utente
    pending['date'].strftime("%Y-%m-%d"),           # Col B: Data (YYYY-MM-DD)
    str(pending['amount']).replace(".", ","),       # Col C: Importo (locale italiana: 50,00)
    str(pending['description']),                    # Col D: Descrizione
    str(category.name),                             # Col E: Categoria
    str(subcategory.name),                          # Col F: Sottocategoria
    str(account.name),                              # Col G: Conto
]]

save_to_sheet(values, "USCITE")
```

### Pattern Esistente

Il bot segue lo stesso pattern della view `index()` in `trantrac/views.py:43-73`:

```python
# Crea values array
values = [[
    str(request.user.display_name),
    form.cleaned_data["date"].strftime("%Y-%m-%d"),
    str(form.cleaned_data["amount"]).replace(".", ","),
    str(form.cleaned_data["description"]),
    str(form.cleaned_data["category"]),
    str(form.cleaned_data["subcategory"]),
    str(form.cleaned_data["bank_account"]),
]]

# Salva
if save_to_sheet(values, "USCITE"):
    CategoryUsage.objects.create(
        user=request.user,
        category=form.cleaned_data["category"],
        subcategory=form.cleaned_data["subcategory"],
    )
```

## Gestione Fallimenti

### PendingTransaction System

Quando `save_to_sheet()` fallisce:

```python
try:
    if save_to_sheet(values, "USCITE"):
        # Success path
        CategoryUsage.objects.create(user=user, category=category, subcategory=subcategory)
        await update.message.reply_text("✅ Transazione salvata!")
    else:
        raise Exception("save_to_sheet returned False")

except Exception as e:
    # Fallback: salva in PendingTransaction
    PendingTransaction.objects.create(
        user=user,
        amount=pending['amount'],
        description=pending['description'],
        category=category,
        subcategory=subcategory,
        account=account,
        date=pending['date'],
        telegram_message_id=update.message.message_id,
        last_error=str(e),
        status='pending'
    )

    await update.message.reply_text(
        "⏳ Transazione salvata, sincronizzazione in corso...\n"
        "Ti avviserò quando sarà completata."
    )
```

### Retry Automatico

**Management Command**: `retry_pending_transactions.py`

```python
from django.core.management.base import BaseCommand
from telegram_bot.models import PendingTransaction
from trantrac.utils import save_to_sheet
import time

class Command(BaseCommand):
    help = 'Retry pending transactions'

    def handle(self, *args, **options):
        pending = PendingTransaction.objects.filter(status='pending').order_by('created_at')

        success_count = 0
        failed_count = 0

        for transaction in pending:
            # Mark as processing
            transaction.status = 'processing'
            transaction.save()

            values = [[
                str(transaction.user.display_name),
                transaction.date.strftime("%Y-%m-%d"),
                str(transaction.amount).replace(".", ","),
                str(transaction.description),
                str(transaction.category.name),
                str(transaction.subcategory.name),
                str(transaction.account.name),
            ]]

            try:
                if save_to_sheet(values, "USCITE"):
                    # Success
                    transaction.status = 'completed'
                    transaction.save()

                    # Create CategoryUsage
                    from trantrac.models import CategoryUsage
                    CategoryUsage.objects.create(
                        user=transaction.user,
                        category=transaction.category,
                        subcategory=transaction.subcategory
                    )

                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ Transaction {transaction.id}'))

                    # TODO: Notify user via Telegram
                    # send_telegram_message(transaction.user.telegram_chat_id,
                    #                       "✅ Transazione sincronizzata!")

                else:
                    raise Exception("save_to_sheet returned False")

            except Exception as e:
                # Fail
                transaction.status = 'pending'
                transaction.retry_count += 1
                transaction.last_error = str(e)

                if transaction.retry_count > 10:
                    transaction.status = 'failed'
                    # TODO: Send email to admin
                    self.stdout.write(self.style.ERROR(f'❌ Transaction {transaction.id} FAILED after 10 retries'))

                transaction.save()
                failed_count += 1
                self.stdout.write(self.style.WARNING(f'⚠️ Transaction {transaction.id} retry {transaction.retry_count}'))

            # Rate limiting: wait 1s between requests
            time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS(f'\nDone: {success_count} success, {failed_count} failed')
        )
```

**Cronjob**: ogni 15 minuti
```bash
*/15 * * * * cd /path/to/trantrac && /path/to/venv/bin/python manage.py retry_pending_transactions >> /var/log/telegram_retry.log 2>&1
```

## Account (Conto) Selection

Il bot usa la stessa logica della view esistente:

```python
# Auto-select account basato su user.display_name
account = Account.objects.filter(name=user.display_name).first() or Account.objects.first()
```

**Esempi**:
- User `display_name="Enrico"` → cerca Account con `name="Enrico"`
- Se non trovato → usa il primo Account disponibile

## CategoryUsage Tracking

Dopo ogni transazione salvata con successo:

```python
CategoryUsage.objects.create(
    user=user,
    category=category,
    subcategory=subcategory
)
```

Questo è utilizzato per suggerimenti futuri (vedi `.beans/04-transaction-flow.md`).

## Limiti e Quota Google Sheets API

### Limiti Standard (Free tier)
- **Read requests**: 100 requests per 100 seconds per user
- **Write requests**: 100 requests per 100 seconds per user

### Mitigazioni
1. **PendingTransaction**: fallback automatico
2. **Retry con backoff**: cronjob ogni 15 min
3. **Rate limiting**: 1s tra retry nel command
4. **Batching** (future): raggruppare più transazioni in un'unica richiesta

### Monitoring

```python
# TODO: Add monitoring
# - Count save_to_sheet() failures
# - Alert if failures > 5% in 1 hour
# - Dashboard con metriche:
#   - Success rate
#   - Pending transactions count
#   - Average retry time
```

## Errori Comuni

### 1. Service Account Permissions

```
Error: The caller does not have permission
```

**Soluzione**: Condividi il Google Sheet con l'email del service account:
1. Apri Google Sheet
2. Share → aggiungi `service-account@project.iam.gserviceaccount.com`
3. Permesso: Editor

### 2. Quota Exceeded

```
Error: Quota exceeded for quota metric 'Write requests'
```

**Soluzione**: Automatica con PendingTransaction + retry

### 3. Invalid Credentials

```
Error: invalid_grant
```

**Soluzione**: Rigenera le credentials del service account

## Testing

### Mock save_to_sheet

```python
# tests/test_handlers.py
from unittest.mock import patch

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_transaction_save_success():
    with patch('telegram_bot.handlers.transaction.save_to_sheet', return_value=True):
        # ... test flow ...
        assert CategoryUsage.objects.filter(user=user).exists()

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_transaction_save_failure():
    with patch('telegram_bot.handlers.transaction.save_to_sheet', side_effect=Exception("Network error")):
        # ... test flow ...
        assert PendingTransaction.objects.filter(user=user, status='pending').exists()
```
