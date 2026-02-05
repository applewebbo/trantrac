"""Management command to configure Telegram webhook"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Set Telegram webhook URL for production"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete existing webhook instead of setting new one",
        )

    def handle(self, *args, **options):
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

        if options["delete"]:
            # Delete webhook
            self.stdout.write("Deleting webhook...")
            bot.delete_webhook()
            self.stdout.write(self.style.SUCCESS("✅ Webhook deleted"))
            return

        # Set webhook
        webhook_url = f"{settings.TELEGRAM_WEBHOOK_URL}/telegram/webhook/"
        secret_token = settings.TELEGRAM_WEBHOOK_SECRET

        self.stdout.write(f"Setting webhook to: {webhook_url}")

        try:
            success = bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                allowed_updates=["message"],
            )

            if success:
                self.stdout.write(self.style.SUCCESS("✅ Webhook set successfully!"))

                # Verify webhook info
                info = bot.get_webhook_info()
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
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to set webhook"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
            raise
