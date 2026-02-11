import logging
import sys
from datetime import date

from django.core.management.base import BaseCommand

from trantrac.models import MonthlyReport

logger = logging.getLogger(__name__)


def get_previous_month(today: date) -> tuple[int, int]:
    """Return (year, month) for the month before today"""
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


class Command(BaseCommand):
    help = "Generate monthly PDF report for a given month (defaults to previous month)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--year", type=int, help="Year of the report (default: auto)"
        )
        parser.add_argument(
            "--month", type=int, help="Month of the report (default: previous month)"
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerate even if report already exists",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without creating files",
        )

    def handle(self, *args, **options):
        year = options["year"]
        month = options["month"]
        force = options["force"]
        dry_run = options["dry_run"]

        # Auto-detect previous month if not provided
        if year is None or month is None:
            prev_year, prev_month = get_previous_month(date.today())
            year = year if year is not None else prev_year
            month = month if month is not None else prev_month

        # Validate month range
        if not (1 <= month <= 12):
            self.stderr.write(
                self.style.ERROR(f"Invalid month: {month}. Must be between 1 and 12.")
            )
            sys.exit(1)

        month_name = MonthlyReport.MONTH_NAMES.get(month, str(month))
        label = f"{month_name} {year}"

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"[dry-run] Would generate report for {label}")
            )
            return

        # Check if report already exists
        existing = MonthlyReport.objects.filter(year=year, month=month).first()
        if existing and existing.pdf_file and not force:
            self.stdout.write(
                self.style.WARNING(
                    f"Report for {label} already exists. Use --force to regenerate."
                )
            )
            logger.info("Report for %s/%s already exists, skipping", month, year)
            sys.exit(2)

        from trantrac.pdf_generator import generate_monthly_report

        logger.info("Generating report for %s/%s", month, year)
        try:
            report = generate_monthly_report(year, month)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error generating report for {label}: {e}")
            )
            logger.error("Error generating report for %s/%s: %s", month, year, e)
            sys.exit(1)

        if report is None:
            self.stdout.write(
                self.style.WARNING(f"No transactions found for {label}. Skipping.")
            )
            logger.info("No transactions for %s/%s, skipping", month, year)
            sys.exit(2)

        self.stdout.write(
            self.style.SUCCESS(f"Report for {label} generated successfully.")
        )
        logger.info(
            "Report for %s/%s generated: income=%.2f expenses=%.2f balance=%.2f",
            month,
            year,
            report.total_income,
            report.total_expenses,
            report.balance,
        )
