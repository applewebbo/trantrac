"""Management command to run bot in polling mode (development)"""

import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from telegram_bot.handlers.auth import (
    handle_contact,
    handle_enrollment_approval,
    handle_start,
)
from telegram_bot.handlers.csv_upload import handle_csv_upload
from telegram_bot.handlers.history import (
    handle_delete_callback,
    handle_recent_transactions,
)
from telegram_bot.handlers.transaction import route_message

BOT_COMMANDS = [
    BotCommand("start", "Collegati o controlla il tuo account"),
    BotCommand("ultime", "Mostra le ultime 5 transazioni inserite"),
]


async def _set_commands(app: Application) -> None:
    await app.bot.set_my_commands(BOT_COMMANDS)


logger = logging.getLogger(__name__)

# Fix for asyncio deprecation warning on Python 3.13+
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


class Command(BaseCommand):
    help = "Run Telegram bot in polling mode (for development)"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("Starting Telegram bot in polling mode...")
        )

        # Build application
        application = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN)
            .post_init(_set_commands)
            .build()
        )

        # Register handlers
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("ultime", handle_recent_transactions))
        application.add_handler(
            CallbackQueryHandler(
                handle_delete_callback,
                pattern="^(delete:|confirm_delete:|cancel_delete)",
            )
        )
        application.add_handler(
            CallbackQueryHandler(
                handle_enrollment_approval,
                pattern="^(approve_enrollment:|reject_enrollment:)",
            )
        )
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        application.add_handler(
            MessageHandler(filters.Document.FileExtension("csv"), handle_csv_upload)
        )
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, route_message)
        )

        # Run polling
        self.stdout.write(
            self.style.SUCCESS(
                "Bot is running. Press Ctrl+C to stop.\n"
                "Send /start to the bot to begin."
            )
        )

        try:
            application.run_polling(allowed_updates=["message", "callback_query"])
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nStopping bot..."))
        finally:
            self.stdout.write(self.style.SUCCESS("Bot stopped."))
