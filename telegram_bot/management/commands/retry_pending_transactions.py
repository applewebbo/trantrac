"""Management command to retry pending transactions"""

import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from telegram_bot.models import PendingTransaction
from trantrac.utils import save_to_sheet

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Retry failed transactions saved as pending"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-retries",
            type=int,
            default=5,
            help="Maximum retry count before marking as failed (default: 5)",
        )

    def handle(self, *args, **options):
        max_retries = options["max_retries"]

        # Get pending transactions to retry
        pending = PendingTransaction.objects.filter(
            Q(status="pending") | Q(status="processing"),
            retry_count__lt=max_retries,
        )

        total = pending.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("No pending transactions to retry."))
            return

        self.stdout.write(f"Found {total} pending transaction(s). Retrying...")

        success_count = 0
        failed_count = 0

        for transaction in pending:
            # Mark as processing
            transaction.status = "processing"
            transaction.save()

            # Format values for Google Sheets
            values = [
                [
                    transaction.date.strftime("%d/%m/%Y"),
                    f"-{transaction.amount}",
                    transaction.description,
                    transaction.category.name,
                    transaction.subcategory.name,
                    transaction.account.name,
                ]
            ]

            try:
                # Try to save
                save_to_sheet(values, "USCITE")

                # Mark as completed
                transaction.status = "completed"
                transaction.save()

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Transaction #{transaction.id}: {transaction.amount}€ "
                        f"- {transaction.description}"
                    )
                )

            except Exception as e:
                # Increment retry count and save error
                transaction.retry_count += 1
                transaction.last_error = str(e)

                # Mark as failed if max retries reached
                if transaction.retry_count >= max_retries:
                    transaction.status = "failed"
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Transaction #{transaction.id} failed after "
                            f"{max_retries} retries: {e}"
                        )
                    )
                else:
                    transaction.status = "pending"
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Transaction #{transaction.id} retry failed "
                            f"(attempt {transaction.retry_count}/{max_retries}): {e}"
                        )
                    )

                transaction.save()
                failed_count += 1

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Total: {total}")
        self.stdout.write(self.style.SUCCESS(f"Successful: {success_count}"))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f"Failed: {failed_count}"))
