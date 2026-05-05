import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from weasyprint import HTML

from trantrac.reports import get_monthly_report_data

MONTH_NAMES = {
    1: "Gennaio",
    2: "Febbraio",
    3: "Marzo",
    4: "Aprile",
    5: "Maggio",
    6: "Giugno",
    7: "Luglio",
    8: "Agosto",
    9: "Settembre",
    10: "Ottobre",
    11: "Novembre",
    12: "Dicembre",
}


def render_report_template(context: dict) -> str:
    """Render monthly report HTML template with the given context"""
    return render_to_string("trantrac/reports/monthly_report.html", context)


def convert_html_to_pdf(html_string: str) -> bytes:
    """Convert HTML string to PDF bytes using WeasyPrint"""
    return HTML(string=html_string).write_pdf()


def save_report_file(pdf_bytes: bytes, year: int, month: int) -> str:
    """Save PDF bytes to media directory and return the relative file path"""
    report_dir = Path(settings.MEDIA_ROOT) / "reports" / str(year)
    report_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4()}.pdf"
    file_path = report_dir / filename
    file_path.write_bytes(pdf_bytes)
    return f"reports/{year}/{filename}"


def generate_monthly_report(year: int, month: int):
    """
    Generate a monthly PDF report for the given year and month.
    Returns a MonthlyReport instance or None if no transactions exist.
    """
    from trantrac.models import MonthlyReport

    data = get_monthly_report_data(year, month)
    if data is None:
        return None

    context = {
        **data,
        "month_name": MONTH_NAMES[month],
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    html_string = render_report_template(context)
    pdf_bytes = convert_html_to_pdf(html_string)
    relative_path = save_report_file(pdf_bytes, year, month)

    report, _created = MonthlyReport.objects.update_or_create(
        year=year,
        month=month,
        defaults={
            "pdf_file": relative_path,
            "generated_at": timezone.now(),
            "total_income": data["total_income"],
            "total_expenses": data["total_expenses"],
            "balance": data["balance"],
            "transaction_count_income": data["count_income"],
            "transaction_count_expenses": data["count_expenses"],
        },
    )
    return report
