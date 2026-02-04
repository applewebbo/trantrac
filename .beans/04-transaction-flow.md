# Flow Transazioni

## Diagramma Completo

```
┌──────────────────────────┐
│ "50/caffè al bar"        │
└──────┬───────────────────┘
       │
       v
┌────────────────────────────┐
│ parse_transaction_message()│
│ → amount: 50               │
│ → description: caffè al bar│
└──────┬─────────────────────┘
       │
       v
┌────────────────────────────────┐
│ get_subcategory_suggestions()  │
│ 1. Storico utente (30gg)       │
│ 2. Fuzzy match descrizione     │
│ → Top 5 sottocategorie         │
└──────┬─────────────────────────┘
       │
       v
┌───────────────────────────────┐
│ Salva in context.user_data    │
│ Mostra elenco numerato:       │
│                               │
│ 💰 50.00€ - caffè al bar      │
│ 📅 04/02/2026                 │
│                               │
│ Scegli sottocategoria:        │
│ 1. Bar (Alimentari)           │
│ 2. Caffè (Alimentari)         │
│ 3. Ristorante (Alimentari)    │
│ 4. Fast Food (Ristoranti)     │
│ 5. Supermercato (Alimentari)  │
│ 0. Altro...                   │
└──────┬────────────────────────┘
       │
       ├─ Utente: "1" ──────────────────────┐
       │                                     │
       └─ Utente: "0" ──────┐               │
                             │               │
                             v               v
                    ┌───────────────┐ ┌─────────────────┐
                    │ Mostra tutte  │ │ Recupera        │
                    │ (paginate)    │ │ sottocategoria  │
                    │ 10 per pagina │ │ selezionata     │
                    └───┬───────────┘ └───┬─────────────┘
                        │                 │
                        │ Utente: "5"     │
                        └────────┬────────┘
                                 │
                                 v
                        ┌─────────────────────────┐
                        │ Mostra conferma finale: │
                        │                         │
                        │ 💰 50.00€ - caffè       │
                        │ 📅 04/02/2026           │
                        │ 🏷️ Alimentari > Bar    │
                        │ 🏦 Enrico               │
                        │                         │
                        │ Conferma? (s/n)         │
                        └─────┬───────────────────┘
                              │
                              ├─ Utente: "s" ───> create_transaction()
                              │                    ↓
                              │              save_to_sheet("USCITE")
                              │                    ↓
                              │              CategoryUsage.create()
                              │                    ↓
                              │              "✅ Transazione salvata!"
                              │
                              └─ Utente: "n" ───> "❌ Transazione annullata"
```

## Parsing Messaggio

**File**: `services/parser.py`

```python
from decimal import Decimal, InvalidOperation

def parse_transaction_message(text: str) -> dict | None:
    """
    Parse: IMPORTO/DESCRIZIONE
    Returns: {'amount': Decimal, 'description': str}
    """
    parts = text.split('/', maxsplit=1)

    if len(parts) != 2:
        return None

    amount_str, description = parts

    # Parse amount (supporta . e , come decimali)
    amount_str = amount_str.strip().replace(',', '.')
    try:
        amount = Decimal(amount_str)
        if amount <= 0:
            return None
    except (ValueError, InvalidOperation):
        return None

    description = description.strip()
    if not description or len(description) > 200:
        return None

    return {
        'amount': amount,
        'description': description
    }
```

**Test Cases**:
- `"50/caffè"` → OK
- `"125.50/spesa"` → OK
- `"15,99/libro"` → OK (virgola)
- `"50/caffè/bar"` → OK (split maxsplit=1, descrizione = "caffè/bar")
- `"50"` → None (no /)
- `"abc/caffè"` → None (importo invalido)
- `"-10/test"` → None (importo negativo)

## Suggerimenti Sottocategorie

**File**: `services/suggestions.py`

```python
from difflib import get_close_matches
from django.db import models
from django.utils import timezone
from datetime import timedelta
from trantrac.models import Subcategory, CategoryUsage

def get_subcategory_suggestions(user, description):
    """
    Suggerisce sottocategorie basandosi su:
    1. Storico utente (CategoryUsage ultimi 30 giorni)
    2. Fuzzy match con descrizione
    """

    # 1. Sottocategorie più usate dall'utente
    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_subcats = CategoryUsage.objects.filter(
        user=user,
        created_at__gte=thirty_days_ago
    ).values('subcategory').annotate(
        usage_count=models.Count('id')
    ).order_by('-usage_count')[:10]

    user_subcat_ids = [s['subcategory'] for s in user_subcats]
    user_suggestions = Subcategory.objects.filter(
        id__in=user_subcat_ids
    ).select_related('category')

    # 2. Fuzzy match con descrizione
    all_subcats = Subcategory.objects.select_related('category').all()
    subcat_names = {s.name.lower(): s for s in all_subcats}

    description_lower = description.lower()
    matches = get_close_matches(
        description_lower,
        subcat_names.keys(),
        n=10,
        cutoff=0.4  # Similarity threshold
    )
    fuzzy_suggestions = [subcat_names[m] for m in matches]

    # 3. Combina e dedup (user suggestions hanno priorità)
    seen = set()
    combined = []

    for s in user_suggestions:
        if s.id not in seen:
            combined.append(s)
            seen.add(s.id)

    for s in fuzzy_suggestions:
        if s.id not in seen:
            combined.append(s)
            seen.add(s.id)

    return combined[:5]  # Top 5
```

**Esempi**:
- User ha usato spesso "Bar" → "Bar" in top 5
- Descrizione "caffè" → fuzzy match con "Caffè", "Bar"
- Descrizione "benzina" → fuzzy match con "Carburante"

## Message Router

**File**: `handlers/transaction.py`

```python
from telegram_bot.models import TelegramAuthSession

async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes text messages to appropriate handler"""
    text = update.message.text.strip()

    # Check auth session
    if TelegramAuthSession.objects.filter(chat_id=update.effective_chat.id).exists():
        await handle_email_message(update, context)
        return

    # Check if awaiting confirmation
    if context.user_data.get('awaiting_confirmation'):
        await handle_final_confirmation(update, context)
        return

    # Check if showing all subcategories (pagination)
    if context.user_data.get('pending_transaction', {}).get('showing_all'):
        if text.lower() in ['n', 'p']:
            await handle_navigation(update, context)
            return
        # Number selection from full list
        await handle_subcategory_selection(update, context)
        return

    # Check if pending transaction (subcategory selection)
    if context.user_data.get('pending_transaction'):
        await handle_subcategory_selection(update, context)
        return

    # New transaction
    if '/' in text:
        await handle_transaction_message(update, context)
        return

    # Unknown
    await update.message.reply_text(
        "Non ho capito. Invia una transazione:\n"
        "Formato: IMPORTO/DESCRIZIONE\n"
        "Esempio: 50/caffè al bar"
    )
```

## Context State Management

**Structure**:
```python
context.user_data = {
    'pending_transaction': {
        'amount': Decimal('50.00'),
        'description': 'caffè al bar',
        'date': date(2026, 2, 4),
        'suggestions': [
            (1, 'Bar', 'Alimentari'),
            (2, 'Caffè', 'Alimentari'),
            (3, 'Ristorante', 'Alimentari'),
            (4, 'Fast Food', 'Ristoranti'),
            (5, 'Supermercato', 'Alimentari'),
        ],
        'subcategory_id': 1,  # Set dopo selezione
        'category_id': 5,     # Set dopo selezione
        'account_id': 3,      # Set dopo selezione
        'showing_all': False,  # True se mostra tutte le sottocategorie
        'all_subcats_page': 0, # Pagina corrente (se showing_all=True)
    },
    'awaiting_confirmation': False,  # True dopo mostra conferma finale
}
```

## Paginazione "Altro..."

```python
async def show_all_subcategories(update, context, page=0):
    """Mostra tutte le sottocategorie paginate"""
    all_subcats = Subcategory.objects.select_related('category').order_by(
        'category__name', 'name'
    )

    per_page = 10
    total = all_subcats.count()
    total_pages = (total + per_page - 1) // per_page

    start = page * per_page
    end = start + per_page
    page_subcats = all_subcats[start:end]

    message = f"Tutte le sottocategorie (Pag. {page + 1}/{total_pages}):\n\n"

    for i, subcat in enumerate(page_subcats, start + 1):
        message += f"{i}. {subcat.name} ({subcat.category.name})\n"

    if page < total_pages - 1:
        message += "\nRispondi con il numero o 'n' per pagina successiva"
    if page > 0:
        message += "\nRispondi con il numero o 'p' per pagina precedente"

    context.user_data['pending_transaction']['all_subcats_page'] = page
    context.user_data['pending_transaction']['showing_all'] = True

    await update.message.reply_text(message)
```
