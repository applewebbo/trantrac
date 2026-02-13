"""Business logic for transaction management"""

import logging
from datetime import date
from decimal import Decimal

from django.utils import timezone

from telegram_bot.models import BotTransaction, PendingTransaction
from trantrac.models import Account, CategoryUsage, Subcategory
from trantrac.utils import delete_row_by_identifier, save_to_sheet

# Column index (0-based) of "Codice identificativo" in USCITE sheet
USCITE_IDENTIFIER_COLUMN = 7

BOT_TRANSACTIONS_LIMIT = 5

logger = logging.getLogger(__name__)


def create_transaction(
    user,
    amount: Decimal,
    description: str,
    subcategory: Subcategory,
    telegram_message_id: int,
    transaction_date: date | None = None,
) -> tuple[bool, str]:
    """
    Create and save transaction to Google Sheets

    Args:
        user: User instance
        amount: Transaction amount (positive for expenses)
        description: Transaction description
        subcategory: Selected Subcategory instance
        telegram_message_id: Telegram message ID for tracking
        transaction_date: Transaction date (default: today)

    Returns:
        Tuple of (success: bool, message: str)
    """
    if transaction_date is None:
        transaction_date = timezone.now().date()

    # Get or create default account for user
    account, _ = Account.objects.get_or_create(
        name=user.display_name or user.email,
        defaults={"name": user.display_name or user.email},
    )

    category = subcategory.category
    bot_transaction = BotTransaction(
        user=user,
        amount=amount,
        description=description,
        category=category,
        subcategory=subcategory,
        account=account,
        date=transaction_date,
        telegram_message_id=telegram_message_id,
    )

    # Format for Google Sheets (USCITE)
    # Columns: Inserito da | Data | Importo | Descrizione | Categoria | Sottocategoria | Conto | Codice identificativo
    # Note: Using DD/MM/YYYY format for date to match Google Sheets locale
    values = [
        [
            str(user.display_name or user.email),  # Inserito da
            transaction_date.strftime("%d/%m/%Y"),  # Data (formato DD/MM/YYYY)
            str(amount).replace(".", ","),  # Importo (con virgola italiana)
            str(description),  # Descrizione
            str(category.name),  # Categoria
            str(subcategory.name),  # Sottocategoria
            str(account.name),  # Conto
            bot_transaction.bot_id,  # Codice identificativo
        ]
    ]

    try:
        # Save to Google Sheets
        logger.info(f"Saving to Google Sheets: {values}")
        save_to_sheet(values, "USCITE")
        logger.info("Successfully saved to Google Sheets")

        # Persist BotTransaction and prune to last 5 per user
        bot_transaction.save()
        _prune_bot_transactions(user)

        # Track usage for future suggestions
        CategoryUsage.objects.create(
            user=user,
            category=category,
            subcategory=subcategory,
        )

        return (
            True,
            f"✅ Salvato: {amount}€ - {description}\n📊 {category.name} > {subcategory.name}",
        )

    except Exception as e:
        # Save as pending for retry
        PendingTransaction.objects.create(
            user=user,
            amount=amount,
            description=description,
            category=category,
            subcategory=subcategory,
            account=account,
            date=transaction_date,
            telegram_message_id=telegram_message_id,
            status="pending",
            last_error=str(e),
        )

        return False, (
            "⚠️ Errore nel salvataggio su Google Sheets.\n"
            "La transazione è stata salvata e verrà ritentata automaticamente."
        )


def delete_bot_transaction(user, bot_id: str) -> tuple[bool, str]:
    """
    Delete a BotTransaction by bot_id.

    Removes the row from Google Sheets first; only deletes the DB record on success.
    Returns (True, success_message) or (False, error_message).
    """
    try:
        tx = BotTransaction.objects.select_related("category", "subcategory").get(
            bot_id=bot_id, user=user
        )
    except BotTransaction.DoesNotExist:
        return False, "❌ Transazione non trovata."

    try:
        delete_row_by_identifier("USCITE", bot_id, USCITE_IDENTIFIER_COLUMN)
    except Exception as e:
        logger.error(f"Failed to delete row from Sheets for {bot_id}: {e}")
        return (
            False,
            "❌ Errore nella cancellazione da Google Sheets. La transazione non è stata eliminata.",
        )

    tx.delete()
    return True, f"✅ Eliminato: {tx.amount}€ — {tx.description}"


def _prune_bot_transactions(user) -> None:
    """Keep only the last BOT_TRANSACTIONS_LIMIT BotTransactions per user."""
    ids_to_keep = (
        BotTransaction.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("id", flat=True)[:BOT_TRANSACTIONS_LIMIT]
    )
    BotTransaction.objects.filter(user=user).exclude(id__in=list(ids_to_keep)).delete()
