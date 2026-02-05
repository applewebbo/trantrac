"""Business logic for transaction management"""

from datetime import date
from decimal import Decimal

from django.utils import timezone

from telegram_bot.models import PendingTransaction
from trantrac.models import Account, CategoryUsage, Subcategory
from trantrac.utils import save_to_sheet


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

    # Format for Google Sheets (USCITE)
    values = [
        [
            transaction_date.strftime("%d/%m/%Y"),
            f"-{amount}",  # Negative for expenses
            description,
            category.name,
            subcategory.name,
            account.name,
        ]
    ]

    try:
        # Save to Google Sheets
        save_to_sheet(values, "USCITE")

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
