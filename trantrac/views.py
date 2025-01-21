from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from trantrac.forms import TransactionForm


@login_required
def index(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            print(amount)
            return render(request, "trantrac/transaction_ok.html")
    else:
        form = TransactionForm()

    context = {"form": form, "user": request.user}
    if request.htmx:
        return render(request, "trantrac/transaction_form.html", context)
    else:
        return render(request, "trantrac/index.html", context)
