"""Management command to configure Telegram webhook"""

import asyncio
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot, BotCommand

logger = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand("start", "Collegati o controlla il tuo account"),
    BotCommand("ultime", "Mostra le ultime 5 transazioni inserite"),
]


class Command(BaseCommand):
    help = "Set Telegram webhook URL for production"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete existing webhook instead of setting new one",
        )

    def handle(self, *args, **options):
        asyncio.run(self._handle_async(options))

    async def _handle_async(self, options):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        async with bot:
            if options["delete"]:
                self.stdout.write("Deleting webhook...")
                await bot.delete_webhook()
                self.stdout.write(self.style.SUCCESS("✅ Webhook deleted"))
                return

            webhook_url = settings.TELEGRAM_WEBHOOK_URL
            secret_token = settings.TELEGRAM_WEBHOOK_SECRET

            self.stdout.write(f"Setting webhook to: {webhook_url}")

            success = await bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                allowed_updates=["message", "callback_query"],
            )

            if not success:
                self.stdout.write(self.style.ERROR("❌ Failed to set webhook"))
                return

            self.stdout.write(self.style.SUCCESS("✅ Webhook set successfully!"))

            await bot.set_my_commands(BOT_COMMANDS)
            self.stdout.write(self.style.SUCCESS("✅ Bot commands registered"))

            info = await bot.get_webhook_info()
            self.stdout.write("\nWebhook Info:")
            self.stdout.write(f"  URL: {info.url}")
            self.stdout.write(f"  Pending updates: {info.pending_update_count}")
            if info.last_error_date:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Last error: {info.last_error_message} "
                        f"at {info.last_error_date}"
                    )
                )
