# Modelli Telegram Bot

## 1. PendingTransaction

Salva transazioni quando Google Sheets fallisce, per retry automatici.

```python
from django.db import models
from django.conf import settings

class PendingTransaction(models.Model):
    """Transazioni fallite da ritentare"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    category = models.ForeignKey('trantrac.Category', on_delete=models.CASCADE)
    subcategory = models.ForeignKey('trantrac.Subcategory', on_delete=models.CASCADE)
    account = models.ForeignKey('trantrac.Account', on_delete=models.CASCADE)
    date = models.DateField()

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    telegram_message_id = models.BigIntegerField()

    STATUS_CHOICES = [
        ('pending', 'In attesa'),
        ('processing', 'In elaborazione'),
        ('completed', 'Completata'),
        ('failed', 'Fallita'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.user} - {self.amount}€ - {self.status}"
```

### Uso

```python
# Creazione quando save_to_sheet fallisce
try:
    save_to_sheet(values, "USCITE")
except Exception as e:
    PendingTransaction.objects.create(
        user=user,
        amount=amount,
        description=description,
        category=category,
        subcategory=subcategory,
        account=account,
        date=date,
        telegram_message_id=message_id,
        last_error=str(e),
        status='pending'
    )
```

### Retry Logic

**Management Command**: `retry_pending_transactions.py`

```python
from django.core.management.base import BaseCommand
from telegram_bot.models import PendingTransaction
from trantrac.utils import save_to_sheet

class Command(BaseCommand):
    help = 'Retry pending transactions'

    def handle(self, *args, **options):
        pending = PendingTransaction.objects.filter(status='pending')

        for transaction in pending:
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
                    transaction.status = 'completed'
                    transaction.save()
                    self.stdout.write(self.style.SUCCESS(f'✅ {transaction.id}'))
                else:
                    transaction.retry_count += 1
                    if transaction.retry_count > 10:
                        transaction.status = 'failed'
                        # TODO: send email to admin
                    transaction.save()
            except Exception as e:
                transaction.retry_count += 1
                transaction.last_error = str(e)
                transaction.save()
```

**Cronjob**: ogni 15 minuti
```bash
*/15 * * * * cd /path && python manage.py retry_pending_transactions
```

## 2. TelegramAuthSession

Vedi `.beans/02-authentication.md`

## 3. CategoryKeyword (Opzionale)

Mapping parole chiave → sottocategorie per suggerimenti automatici.

```python
class CategoryKeyword(models.Model):
    """Parole chiave per auto-categorizzazione"""

    keyword = models.CharField(max_length=100, db_index=True)
    subcategory = models.ForeignKey('trantrac.Subcategory', on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        unique_together = [('keyword', 'subcategory')]
        ordering = ['-priority', 'keyword']

    def __str__(self):
        return f"{self.keyword} → {self.subcategory.name}"
```

### Uso

```python
# Esempio: "benzina" → Carburante
CategoryKeyword.objects.create(
    keyword="benzina",
    subcategory=carburante_subcat,
    priority=10
)

# Lookup
keywords = CategoryKeyword.objects.filter(
    keyword__icontains=description
).select_related('subcategory')
```

### Popolamento Iniziale

```python
# management/commands/populate_keywords.py
KEYWORDS = {
    'benzina': ('Trasporti', 'Carburante'),
    'q8': ('Trasporti', 'Carburante'),
    'esso': ('Trasporti', 'Carburante'),
    'caffè': ('Alimentari', 'Bar'),
    'cappuccino': ('Alimentari', 'Bar'),
    'pizza': ('Alimentari', 'Ristorante'),
    'supermercato': ('Alimentari', 'Supermercato'),
    'esselunga': ('Alimentari', 'Supermercato'),
    # ... etc
}
```

## Admin Registration

**File**: `telegram_bot/admin.py`

```python
from django.contrib import admin
from .models import PendingTransaction, TelegramAuthSession, CategoryKeyword

@admin.register(PendingTransaction)
class PendingTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'description', 'status', 'retry_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['description', 'user__email']
    readonly_fields = ['created_at', 'telegram_message_id']

@admin.register(TelegramAuthSession)
class TelegramAuthSessionAdmin(admin.ModelAdmin):
    list_display = ['chat_id', 'phone_number', 'created_at', 'is_expired']
    readonly_fields = ['created_at']

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True

@admin.register(CategoryKeyword)
class CategoryKeywordAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'subcategory', 'priority']
    list_filter = ['subcategory__category']
    search_fields = ['keyword', 'subcategory__name']
```
