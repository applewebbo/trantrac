from datetime import datetime, timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Field, Layout, Submit
from django import forms
from django.urls import reverse_lazy

from trantrac.models import Account, Category, Subcategory

HTML_ADD_BUTTON = """
    <a href="{% url 'add_category' %}" class='btn btn-sm btn-primary'>{% heroicon_mini 'plus' %}</a>
    """
HTML_ADD_SUBCATEGORY_BUTTON = """
    <a href="{% url 'add_subcategory' %}?category="
       class='btn btn-sm btn-primary'
       x-bind:class="{ 'btn-disabled': !hasCategory }"
       @click.prevent="window.location.href = '{% url 'add_subcategory' %}?category=' + $refs.categorySelect.value">
        {% heroicon_mini 'plus' %}
    </a>
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
    subcategory = forms.ModelChoiceField(
        queryset=Subcategory.objects.none(),
        label="Sottocategoria",
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
        self.fields["subcategory"].empty_label = "Seleziona sottocategoria"
        # If category is selected, filter subcategories
        if "category" in self.data:
            try:
                category_id = int(self.data.get("category"))
                self.fields["subcategory"].queryset = Subcategory.objects.filter(
                    category_id=category_id
                ).order_by("name")
            except (ValueError, TypeError):
                pass
        self.helper.field_class = "grow mb-3"
        self.helper.layout = Layout(
            Div(
                Field("amount", css_class="bg-gray-50"),
                Field("date", css_class="bg-gray-50"),
                Field("description", css_class="bg-gray-50"),
                Div(
                    Field(
                        "category",
                        x_ref="categorySelect",
                        autocomplete="off",
                        **{
                            "@change": "hasCategory = $event.target.value !== ''",
                        },
                    ),
                    HTML(HTML_ADD_BUTTON),
                    css_class="flex gap-x-6 gap-y-2 items-center",
                    hx_get=reverse_lazy("load_subcategories"),
                    hx_trigger="change",
                    hx_target="#id_subcategory",
                    hx_include="[name='category']",
                ),
                Div(
                    Field(
                        "subcategory",
                        css_class="bg-gray-50",
                        **{"x-bind:disabled": "!hasCategory"},
                    ),
                    HTML(HTML_ADD_SUBCATEGORY_BUTTON),
                    css_class="flex gap-x-6 gap-y-2 items-center",
                ),
                "bank_account",
                Submit(
                    "submit",
                    "Salva",
                    css_class="w-full mt-3",
                ),
                x_data="{ hasCategory: false }",
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


class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory
        fields = ["name", "category"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.label_class = "block text-base-content text-sm font-bold mb-2"
        self.fields["name"].label = "Sottocategoria"
        self.fields["category"].label = "Categoria"
        self.helper.layout = Layout(
            Field("name", css_class="bg-gray-50"),
            Field("category", css_class="bg-gray-50"),
            Submit(
                "submit",
                "Aggiungi",
                css_class="w-full mt-3",
            ),
        )


class CsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="File CSV", help_text="Scarica il file nel formato csv a 1 colonna"
    )

    def clean_file(self):
        file = self.cleaned_data.get("file")
        ext = file.name.split(".")[-1].lower()
        if ext not in ["csv"]:
            raise forms.ValidationError("Il file deve essere in formato csv")
        return file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields["csv_file"].label = False
        self.helper.help_text_inline = True
        self.helper.layout = Layout(
            Field(
                "csv_file", css_class="bg-gray-50 file-input file-input-primary w-full"
            ),
            Submit(
                "submit",
                "Carica",
                css_class="w-full mt-3",
            ),
        )
