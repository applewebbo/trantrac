"""Handlers for bot transaction history and deletion"""

import logging

from asgiref.sync import sync_to_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from telegram_bot.models import BotTransaction
from telegram_bot.services.transaction_service import delete_bot_transaction
from telegram_bot.utils.auth import get_approved_user, reply_if_not_enrolled

logger = logging.getLogger(__name__)


async def handle_recent_transactions(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Show the last 5 transactions inserted via bot for the authenticated user."""
    if await reply_if_not_enrolled(update):
        return

    user = await get_approved_user(update)

    transactions = await sync_to_async(
        lambda: list(
            BotTransaction.objects.filter(user=user)
            .select_related("category", "subcategory")
            .order_by("-created_at")[:5]
        )
    )()

    if not transactions:
        await update.message.reply_text("📋 Nessuna transazione inserita via bot.")
        return

    message_lines = ["📋 *Ultime transazioni inserite via bot:*\n"]
    keyboard = []

    for i, tx in enumerate(transactions, start=1):
        date_str = tx.date.strftime("%d/%m/%Y")
        message_lines.append(
            f"{i}. {date_str} — *{tx.amount}€* — {tx.description}\n"
            f"   📊 {tx.category.name} > {tx.subcategory.name}"
        )
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🗑 Elimina #{i}", callback_data=f"delete:{tx.bot_id}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "\n".join(message_lines),
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def handle_delete_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle inline button callback for transaction deletion.

    Callback data format: 'delete:<bot_id>' or 'confirm_delete:<bot_id>' or 'cancel_delete'.
    """
    query = update.callback_query
    await query.answer()

    if await reply_if_not_enrolled(update):
        return

    user = await get_approved_user(update)

    data = query.data

    if data.startswith("delete:"):
        bot_id = data.split(":", 1)[1]
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Sì, elimina", callback_data=f"confirm_delete:{bot_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ No, annulla", callback_data="cancel_delete"
                    ),
                ]
            ]
        )
        await query.edit_message_reply_markup(reply_markup=keyboard)

    elif data.startswith("confirm_delete:"):
        bot_id = data.split(":", 1)[1]
        success, message = await sync_to_async(delete_bot_transaction)(user, bot_id)
        await query.edit_message_text(message)

    elif data == "cancel_delete":
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("↩️ Cancellazione annullata.")
