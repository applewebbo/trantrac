from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from trantrac.forms import CategoryForm, CsvUploadForm, SubcategoryForm, TransactionForm
from trantrac.models import Category, CategoryUsage, Subcategory
from trantrac.utils import import_csv_to_sheet, save_to_sheet, get_sheet_data


def get_recent_categories(limit=6):
    """Get last N used category+subcategory pairs (global)"""
    return (
        CategoryUsage.objects.values(
            "category", "subcategory", "subcategory__name", "category__name"
        )
        .distinct()
        .order_by("-created_at")[:limit]
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

            if save_to_sheet(values, "USCITE"):
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
            success, message = import_csv_to_sheet(
                request.FILES["csv_file"], request.user
            )
            messages.add_message(
                request,
                messages.SUCCESS if success else messages.ERROR,
                message,
            )

            return HttpResponse(status=204, headers={"HX-Redirect": reverse("index")})
    else:
        form = CsvUploadForm()
    return TemplateResponse(request, "trantrac/upload_csv.html", {"form": form})


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
    if sheet_data:
        for row in sheet_data:
            category_name = row[0] if row else None
            subcategory_name = row[1] if len(row) > 1 else None

            if category_name:
                # Get or create category
                category, _ = Category.objects.get_or_create(name=category_name)

                # Create subcategory if it exists
                if subcategory_name:
                    Subcategory.objects.get_or_create(
                        name=subcategory_name,
                        category=category,
                        defaults={"skip_sheet_save": True},
                    )

        messages.add_message(
            request, messages.SUCCESS, "Categorie aggiornate con successo"
        )
    else:
        messages.add_message(
            request, messages.ERROR, "Impossibile recuperare i dati dal foglio"
        )

    return HttpResponse(status=204, headers={"HX-Redirect": reverse("index")})
