"""Management command to send Telegram reminders to approved users."""

import asyncio
import logging
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand
from telegram import Bot

from users.models import User

logger = logging.getLogger(__name__)

MESSAGES = {
    "monthly_user": (
        "📅 Reminder mensile: è il primo del mese!\n"
        "Ricordati di inserire le spese del mese scorso entro 3 giorni. 💸"
    ),
    "monthly_admin": (
        "📅 Reminder mensile: è il primo del mese!\n"
        "Ricordati di importare il CSV della banca entro il 5 del mese. 📂"
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
            help="Type of reminder: 'monthly' (1st of month) or 'weekly' (Monday)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be sent without actually sending",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send even if today is not the 1st of the month (monthly only)",
        )

    def handle(self, *args, **options):
        if options["reminder_type"] == "monthly" and not options.get("force"):
            today = date.today()
            if today.day != 1:
                self.stdout.write(
                    self.style.WARNING(
                        f"Today is {today.day}, not the 1st of the month. Skipping."
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

        if not approved_users:
            self.stdout.write(self.style.WARNING("No approved Telegram users found."))
            logger.info(
                "No approved Telegram users found for %s reminder", reminder_type
            )
            return

        if dry_run:
            admin_count = sum(1 for u in approved_users if u.is_staff or u.is_superuser)
            user_count = len(approved_users) - admin_count
            if reminder_type == "monthly":
                self.stdout.write(
                    self.style.WARNING(
                        f"[dry-run] Would send monthly reminder to "
                        f"{user_count} user(s) and {admin_count} admin(s):\n"
                        f"User message: {MESSAGES['monthly_user']}\n"
                        f"Admin message: {MESSAGES['monthly_admin']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"[dry-run] Would send {reminder_type} reminder to "
                        f"{len(approved_users)} user(s):\n{MESSAGES['weekly']}"
                    )
                )
            return

        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        sent = 0
        failed = 0

        async with bot:
            for user in approved_users:
                if reminder_type == "monthly":
                    message = (
                        MESSAGES["monthly_admin"]
                        if (user.is_staff or user.is_superuser)
                        else MESSAGES["monthly_user"]
                    )
                else:
                    message = MESSAGES["weekly"]

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
