"""Authentication helpers for Telegram bot handlers."""

from asgiref.sync import sync_to_async
from telegram import Update

from users.models import User


async def get_approved_user(update: Update) -> User | None:
    """Return User if their telegram_status is 'approved', else None."""
    chat_id = update.effective_chat.id
    try:
        return await sync_to_async(User.objects.get)(
            telegram_chat_id=chat_id,
            telegram_status=User.TELEGRAM_STATUS_APPROVED,
        )
    except User.DoesNotExist:
        return None


async def reply_if_not_enrolled(update: Update) -> bool:
    """
    Check enrollment status and send the appropriate reply if not approved.

    Returns True when the caller should exit (user is not approved).
    Returns False when the user is approved and can proceed.
    """
    chat_id = update.effective_chat.id
    user = await sync_to_async(User.objects.filter(telegram_chat_id=chat_id).first)()

    if user is None:
        msg = "❌ Account non collegato.\nUsa /start per collegare il tuo account."
    elif user.telegram_status == User.TELEGRAM_STATUS_PENDING:
        msg = (
            "⏳ Richiesta in attesa di approvazione.\nTi notificherò appena confermata."
        )
    else:
        return False

    if update.callback_query:
        await update.callback_query.edit_message_text(msg)
    else:
        await update.message.reply_text(msg)

    return True
