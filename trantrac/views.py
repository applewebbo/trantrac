from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from google.oauth2 import service_account
from googleapiclient.discovery import build

from trantrac.forms import TransactionForm

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def save_to_sheet(values):
    credentials = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SHEETS_CREDENTIALS, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=credentials)

    try:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=settings.GOOGLE_SHEETS_SPREADSHEET_ID,
                range="TRANSAZIONI!A:C",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            )
            .execute()
        )

        return result.get("updates").get("updatedRows") == 1
    finally:
        service.close()


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
                ]
            ]

            if save_to_sheet(values):
                return render(request, "trantrac/transaction_ok.html")
            else:
                return render(request, "trantrac/transaction_error.html")

    else:
        form = TransactionForm()

    context = {"form": form, "user": request.user}
    if request.htmx:
        return render(request, "trantrac/transaction_form.html", context)
    else:
        return render(request, "trantrac/index.html", context)
