"""CSV upload handler for Telegram bot (admin only)."""

import io
import logging

from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.utils.auth import get_approved_user, reply_if_not_enrolled
from trantrac.utils import import_csv_to_sheet

logger = logging.getLogger(__name__)


class _TelegramFileWrapper:
    """Wraps a BytesIO to match the .file interface expected by import_csv_to_sheet."""

    def __init__(self, bio: io.BytesIO) -> None:
        self.file = bio


async def handle_csv_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle CSV file uploads from admin users.

    Only staff users can upload CSV files. The file is processed using the
    same import logic as the web upload.
    """
    if await reply_if_not_enrolled(update):
        return

    user = await get_approved_user(update)

    if not user.is_staff:
        await update.message.reply_text("❌ Funzione riservata agli admin.")
        return

    document = update.message.document
    if not document.file_name or not document.file_name.lower().endswith(".csv"):
        await update.message.reply_text("❌ Invia un file con estensione .csv")
        return

    await update.message.reply_text("⏳ Elaborazione CSV in corso...")

    try:
        tg_file = await context.bot.get_file(document.file_id)
        bio = io.BytesIO()
        await tg_file.download_to_memory(out=bio)
        bio.seek(0)

        wrapper = _TelegramFileWrapper(bio)
        success, message = await sync_to_async(import_csv_to_sheet)(wrapper, user)

        prefix = "✅" if success else "❌"
        await update.message.reply_text(f"{prefix} {message}")

    except Exception:
        logger.exception("Error processing CSV upload from bot")
        await update.message.reply_text(
            "❌ Errore durante l'elaborazione del file. Riprova più tardi."
        )
