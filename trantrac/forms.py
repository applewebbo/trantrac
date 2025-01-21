from datetime import datetime, timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms

from trantrac.models import Account, Category


class DateInput(forms.widgets.DateInput):
    input_type = "date"


class TransactionForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Importo")
    date = forms.DateField(widget=DateInput(), label="Data")
    description = forms.CharField(max_length=200, label="Descrizione")
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(), label="Categoria"
    )
    bank_account = forms.ModelChoiceField(queryset=Account.objects.all(), label="Conto")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["date"].initial = datetime.now(timezone.utc)
        self.fields["bank_account"].initial = Account.objects.first()
        self.helper.layout = Layout(
            "amount",
            "date",
            "description",
            "category",
            "bank_account",
            Submit(
                "submit",
                "Salva",
                css_class="w-full mt-3",
            ),
        )
