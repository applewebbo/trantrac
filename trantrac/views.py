from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from trantrac.forms import TransactionForm


@login_required
def index(request):
    form = TransactionForm(request.POST or None)
    user = request.user
    context = {"form": form, "user": user}
    return render(request, "trantrac/index.html", context)
