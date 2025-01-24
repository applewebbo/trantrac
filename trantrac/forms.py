from datetime import datetime, timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout, Submit, Field
from django import forms

from trantrac.models import Account, Category

HTML_ADD_BUTTON = """
    <a href="{% url 'add_category' %}" class='btn btn-sm btn-primary'>{% heroicon_mini 'plus' %}</a>
    """


class DateInput(forms.widgets.DateInput):
    input_type = "date"

    # return ISO format date with LANGUAGE_CODE it-it
    def format_value(self, value):
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        return value.strftime("%Y-%m-%d")


class TransactionForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, label="Importo")
    date = forms.DateField(widget=DateInput(), label="Data")
    description = forms.CharField(max_length=200, label="Descrizione")
    category = forms.ModelChoiceField(
        queryset=Category.objects.all().order_by("name"), label="Categoria"
    )
    bank_account = forms.ModelChoiceField(queryset=Account.objects.all(), label="Conto")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.label_class = "block text-base-content text-sm font-bold mb-2"
        self.fields["date"].initial = datetime.now(timezone.utc)
        self.fields["bank_account"].initial = Account.objects.first()
        self.fields["category"].empty_label = "Seleziona categoria"
        self.helper.field_class = "grow mb-3"
        self.helper.layout = Layout(
            Field("amount", css_class="bg-gray-50"),
            Field("date", css_class="bg-gray-50"),
            Field("description", css_class="bg-gray-50"),
            Div(
                "category",
                HTML(HTML_ADD_BUTTON),
                css_class="flex gap-x-6 gap-y-2 items-center",
            ),
            "bank_account",
            Submit(
                "submit",
                "Salva",
                css_class="w-full mt-3",
            ),
        )


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.label_class = "block text-base-content text-sm font-bold mb-2"
        self.fields["name"].label = "Categoria"
        self.helper.layout = Layout(
            Field("name", css_class="bg-gray-50"),
            Submit(
                "submit",
                "Aggiungi",
                css_class="w-full mt-3",
            ),
        )
