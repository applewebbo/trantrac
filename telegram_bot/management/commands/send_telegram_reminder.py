"""Management command to send Telegram reminders to approved users."""

import asyncio
import calendar
import logging
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot

from users.models import User

logger = logging.getLogger(__name__)

MESSAGES = {
    "monthly": (
        "📅 Reminder mensile: oggi è l'ultimo giorno del mese!\n"
        "Ricordati di inserire tutte le spese prima della mezzanotte. 💸"
    ),
    "weekly": (
        "📋 Reminder settimanale: è iniziata una nuova settimana!\n"
        "Hai inserito tutte le spese della settimana scorsa? 💸"
    ),
}


class Command(BaseCommand):
    help = "Send Telegram reminder to all approved users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--type",
            dest="reminder_type",
            choices=["monthly", "weekly"],
            required=True,
            help="Type of reminder: 'monthly' (last day of month) or 'weekly' (Monday)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send even if today is not the last day of the month (monthly only)",
        )

    def handle(self, *args, **options):
        if options["reminder_type"] == "monthly" and not options.get("force"):
            today = date.today()
            last_day = calendar.monthrange(today.year, today.month)[1]
            if today.day != last_day:
                self.stdout.write(
                    self.style.WARNING(
                        f"Today is {today.day}, not the last day of the month ({last_day}). Skipping."
                    )
                )
                return

        approved_users = list(
            User.objects.filter(
                telegram_status=User.TELEGRAM_STATUS_APPROVED,
                telegram_chat_id__isnull=False,
            )
        )
        asyncio.run(self._handle_async(options, approved_users))

    async def _handle_async(self, options, approved_users):
        reminder_type = options["reminder_type"]
        dry_run = options["dry_run"]

        message = MESSAGES[reminder_type]

        if not approved_users:
            self.stdout.write(self.style.WARNING("No approved Telegram users found."))
            logger.info(
                "No approved Telegram users found for %s reminder", reminder_type
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[dry-run] Would send {reminder_type} reminder to "
                    f"{len(approved_users)} user(s):\n{message}"
                )
            )
            return

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        sent = 0
        failed = 0

        async with bot:
            for user in approved_users:
                try:
                    await bot.send_message(chat_id=user.telegram_chat_id, text=message)
                    sent += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Sent to {user.email} (chat {user.telegram_chat_id})"
                        )
                    )
                    logger.info("Reminder sent to user %s", user.email)
                except Exception as e:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"Failed to send to {user.email}: {e}")
                    )
                    logger.error(
                        "Failed to send reminder to user %s: %s", user.email, e
                    )

        self.stdout.write(f"\nSummary: {sent} sent, {failed} failed")
        logger.info("%s reminder: %d sent, %d failed", reminder_type, sent, failed)
