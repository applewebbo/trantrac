from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from trantrac.forms import CategoryForm, CsvUploadForm, TransactionForm
from trantrac.utils import import_csv_to_sheet, save_to_sheet


@login_required
def index(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            values = [
                [
                    str(request.user.display_name),
                    form.cleaned_data["date"].strftime("%Y-%m-%d"),
                    str(form.cleaned_data["amount"]).replace(".", ","),
                    str(form.cleaned_data["description"]),
                    str(form.cleaned_data["category"]),
                    str(form.cleaned_data["bank_account"]),
                ]
            ]

            if save_to_sheet(values):
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
        form = TransactionForm()

    context = {"form": form, "user": request.user}
    if request.htmx:
        return TemplateResponse(request, "trantrac/transaction_form.html", context)
    else:
        return TemplateResponse(request, "trantrac/index.html", context)


def add_category(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("index")
    return TemplateResponse(request, "trantrac/add_category.html", {"form": form})


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


@login_required
def refresh_categories(request):
    pass
