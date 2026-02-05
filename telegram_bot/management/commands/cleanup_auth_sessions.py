"""Management command to cleanup expired auth sessions"""

import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from telegram_bot.models import TelegramAuthSession

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete expired Telegram auth sessions (>5 minutes old)"

    def handle(self, *args, **options):
        # Get all sessions
        all_sessions = TelegramAuthSession.objects.all()
        total = all_sessions.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No auth sessions found."))
            return

        # Find expired sessions
        expired = [session for session in all_sessions if session.is_expired()]
        expired_count = len(expired)

        if expired_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No expired sessions found (total: {total} active)."
                )
            )
            return

        # Delete expired sessions
        self.stdout.write(f"Found {expired_count} expired session(s). Deleting...")

        for session in expired:
            age_minutes = (timezone.now() - session.created_at).total_seconds() / 60
            self.stdout.write(
                f"  Deleting session {session.chat_id} (age: {age_minutes:.1f} minutes)"
            )
            session.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Deleted {expired_count} expired session(s). "
                f"{total - expired_count} active session(s) remaining."
            )
        )
