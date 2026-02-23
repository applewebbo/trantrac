import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from trantrac.forms import CategoryForm, CsvUploadForm, SubcategoryForm, TransactionForm
from trantrac.models import Category, CategoryUsage, MonthlyReport, Subcategory
from trantrac.utils import (
    MAX_CSV_SIZE,
    get_sheet_data,
    import_csv_to_sheet,
    save_to_sheet,
)

logger = logging.getLogger(__name__)


def get_recent_categories(limit=6):
    """Get last N used category+subcategory pairs (global)"""
    from django.db.models import Max

    return (
        CategoryUsage.objects.values(
            "category", "subcategory", "subcategory__name", "category__name"
        )
        .annotate(last_used=Max("created_at"))
        .order_by("-last_used")[:limit]
    )


def get_most_used_categories(limit=6):
    """Get top N most used category+subcategory pairs (global)"""
    return (
        CategoryUsage.objects.values(
            "category", "subcategory", "subcategory__name", "category__name"
        )
        .annotate(usage_count=Count("id"))
        .order_by("-usage_count")[:limit]
    )


@login_required
def index(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            values = [
                [
                    str(request.user.display_name),
                    form.cleaned_data["date"].strftime("%Y-%m-%d"),
                    str(form.cleaned_data["amount"]).replace(".", ","),
                    str(form.cleaned_data["description"]),
                    str(form.cleaned_data["category"]),
                    str(form.cleaned_data["subcategory"]),
                    str(form.cleaned_data["bank_account"]),
                ]
            ]

            try:
                success = save_to_sheet(values, "USCITE")
            except Exception:
                logger.exception("Unexpected error saving transaction to sheet")
                success = False

            if success:
                # Track category usage
                CategoryUsage.objects.create(
                    user=request.user,
                    category=form.cleaned_data["category"],
                    subcategory=form.cleaned_data["subcategory"],
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Transazione aggiunta con successo",
                )
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "Ops.. qualcosa è andato storto",
                )
            return HttpResponse(status=204, headers={"HX-Refresh": "true"})

    else:
        form = TransactionForm(user=request.user)

    recent_categories = get_recent_categories()
    most_used_categories = get_most_used_categories()
    has_category_data = bool(recent_categories or most_used_categories)

    context = {
        "form": form,
        "user": request.user,
        "recent_categories": recent_categories,
        "most_used_categories": most_used_categories,
        "has_category_data": has_category_data,
    }
    if request.htmx:
        return TemplateResponse(request, "trantrac/transaction_form.html", context)
    else:
        return TemplateResponse(request, "trantrac/index.html", context)


def add_category(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Categoria aggiunta con successo",
        )
        return redirect("index")
    return TemplateResponse(request, "trantrac/add_category.html", {"form": form})


def add_subcategory(request):
    category_id = request.GET.get("category")
    initial = {"category": category_id} if category_id else {}

    if request.method == "POST":
        form = SubcategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Sottocategoria aggiunta con successo",
            )
            return redirect("index")
    else:
        form = SubcategoryForm(initial=initial)

    return TemplateResponse(request, "trantrac/add_subcategory.html", {"form": form})


@login_required
def upload_csv(request):
    if request.method == "POST":
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES["csv_file"]
            if csv_file.size > MAX_CSV_SIZE:
                messages.add_message(
                    request, messages.ERROR, "File troppo grande (max 2MB)"
                )
                return HttpResponse(
                    status=204, headers={"HX-Redirect": reverse("index")}
                )
            success, message = import_csv_to_sheet(csv_file, request.user)
            messages.add_message(
                request,
                messages.SUCCESS if success else messages.ERROR,
                message,
            )

            return HttpResponse(status=204, headers={"HX-Redirect": reverse("index")})
    else:
        form = CsvUploadForm()

    context = {"form": form}
    if request.htmx:
        return TemplateResponse(request, "trantrac/upload_csv.html", context)
    else:
        return TemplateResponse(request, "trantrac/upload_csv_page.html", context)


def load_subcategories(request):
    category_id = request.GET.get("category")
    if category_id:
        subcategories = Subcategory.objects.filter(category_id=category_id).order_by(
            "name"
        )
    else:
        subcategories = Subcategory.objects.none()
    return TemplateResponse(
        request, "trantrac/subcategory_choices.html", {"subcategories": subcategories}
    )


@login_required
def refresh_categories(request):
    sheet_data = get_sheet_data("CATEGORIE", "A2:B")
    if not sheet_data:
        messages.add_message(
            request, messages.ERROR, "Impossibile recuperare i dati dal foglio"
        )
        return HttpResponse(status=204, headers={"HX-Redirect": reverse("index")})

    # Counters for feedback
    categories_created = 0
    subcategories_created = 0
    skipped = 0
    seen_pairs = set()

    for row in sheet_data:
        # Stop if row is completely empty
        if not row:
            break

        category_name = row[0].strip() if row[0] else ""
        subcategory_name = row[1].strip() if len(row) > 1 and row[1] else None

        # Skip if no category name after stripping
        if not category_name:
            continue

        # Skip duplicates
        pair = (category_name, subcategory_name)
        if pair in seen_pairs:
            skipped += 1
            continue
        seen_pairs.add(pair)

        # Get or create category
        category, cat_created = Category.objects.get_or_create(name=category_name)
        if cat_created:
            categories_created += 1

        # Create subcategory if it exists
        if subcategory_name:
            _, sub_created = Subcategory.objects.get_or_create(
                name=subcategory_name,
                category=category,
                defaults={"skip_sheet_save": True},
            )
            if sub_created:
                subcategories_created += 1

    # Detailed feedback message
    feedback_parts = []
    if categories_created > 0:
        feedback_parts.append(f"{categories_created} nuove categorie")
    if subcategories_created > 0:
        feedback_parts.append(f"{subcategories_created} nuove sottocategorie")
    if skipped > 0:
        feedback_parts.append(f"{skipped} duplicate saltate")

    if feedback_parts:
        message = f"Sincronizzazione completata: {', '.join(feedback_parts)}"
    else:
        message = "Nessuna modifica necessaria"

    messages.add_message(request, messages.SUCCESS, message)
    return HttpResponse(status=204, headers={"HX-Redirect": reverse("index")})


@login_required
def reports_list(request):
    reports = MonthlyReport.objects.order_by("-year", "-month")
    available_years = sorted(
        set(reports.values_list("year", flat=True)),
        reverse=True,
    )
    context = {
        "reports": reports,
        "months": MonthlyReport.MONTH_NAMES,
        "available_years": available_years,
    }
    if request.method == "POST":
        year = request.POST.get("year")
        month = request.POST.get("month")
        try:
            report = MonthlyReport.objects.get(year=int(year), month=int(month))
            if not report.pdf_file:
                messages.add_message(
                    request,
                    messages.ERROR,
                    "PDF non ancora disponibile per questo periodo.",
                )
                return TemplateResponse(request, "trantrac/reports_list.html", context)
            return redirect("download_report", download_uuid=report.download_uuid)
        except MonthlyReport.DoesNotExist, TypeError, ValueError:
            messages.add_message(
                request,
                messages.ERROR,
                "Nessun report disponibile per il periodo selezionato.",
            )
    return TemplateResponse(request, "trantrac/reports_list.html", context)


@login_required
def download_report(request, download_uuid):
    report = get_object_or_404(MonthlyReport, download_uuid=download_uuid)
    if not report.pdf_file:
        raise Http404
    return FileResponse(
        report.pdf_file.open("rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=f"report_{report.year}_{report.month:02d}.pdf",
    )
