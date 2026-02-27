from datetime import datetime, timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Field, Layout, Submit
from django import forms
from django.urls import reverse_lazy

from trantrac.models import Account, Category, Subcategory

HTML_ADD_BUTTON = "{% include 'includes/add_category_button.html' %}"
HTML_ADD_SUBCATEGORY_BUTTON = "{% include 'includes/add_subcategory_button.html' %}"
HTML_QUICK_CATEGORIES_START = "{% include 'includes/quick_categories_start.html' %}"
HTML_QUICK_CATEGORIES_END = "{% include 'includes/quick_categories_end.html' %}"
HTML_CATEGORY_SUGGESTIONS = '<div id="category-suggestions"></div>'


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
    bank_account = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        label="Conto",
        widget=forms.HiddenInput(),
    )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError(
                "Il valore inserito deve essere maggiore di zero"
            )
        return amount

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.label_class = "block text-base-content text-sm font-bold mb-2"
        self.fields["date"].initial = datetime.now(timezone.utc)
        # Set initial bank account based on user's display name
        if user and user.display_name:
            matching_account = Account.objects.filter(name=user.display_name).first()
            self.fields["bank_account"].initial = (
                matching_account or Account.objects.first()
            )
        else:
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
            except ValueError, TypeError:
                pass
        self.helper.field_class = "grow mb-3"

        self.helper.layout = Layout(
            Div(
                Div(
                    Div(
                        HTML(
                            '<label class="block text-base-content text-sm font-bold mb-2">Importo</label>'
                        ),
                        HTML("""
                            <label class="flex gap-2 items-center w-full input input-bordered">
                                <input type="number" step="0.01" name="amount" id="id_amount"
                                       class="grow bg-transparent focus:outline-none" placeholder="0.00" required />
                                {% heroicon_outline 'currency-euro' class='w-6 h-6 opacity-50' %}
                            </label>
                        """),
                        css_class="grow",
                    ),
                    Field(
                        "date",
                        wrapper_class="grow",
                    ),
                    css_class="flex flex-col md:flex-row gap-3 mb-3",
                ),
                Field(
                    "description",
                    **{
                        "hx-get": str(reverse_lazy("suggest_categories")),
                        "hx-trigger": "keyup changed delay:400ms",
                        "hx-target": "#category-suggestions",
                        "hx-include": "[name='description']",
                    },
                ),
                HTML(HTML_CATEGORY_SUGGESTIONS),
                HTML(HTML_QUICK_CATEGORIES_START),
                Div(
                    Field(
                        "category",
                        x_ref="categorySelect",
                        css_id="id_category",
                        autocomplete="off",
                        **{
                            "@change": "hasCategory = $event.target.value !== ''",
                        },
                    ),
                    HTML(HTML_ADD_BUTTON),
                    css_class="flex gap-x-6 gap-y-2 items-center",
                    hx_get=reverse_lazy("load_subcategories"),
                    hx_trigger="change from:#id_category",
                    hx_target="#id_subcategory",
                    hx_indicator="#subcategory-loading",
                    hx_vals='js:{"category": event.target.value}',
                ),
                Div(
                    Field(
                        "subcategory",
                        css_class="bg-base-200",
                        **{"x-bind:disabled": "!hasCategory"},
                    ),
                    HTML(
                        '<span id="subcategory-loading" class="loading loading-spinner loading-sm htmx-indicator text-primary"></span>'
                    ),
                    HTML(HTML_ADD_SUBCATEGORY_BUTTON),
                    css_class="flex gap-x-6 gap-y-2 items-center",
                ),
                HTML(HTML_QUICK_CATEGORIES_END),
                Field("bank_account"),
                Submit(
                    "submit",
                    "Aggiungi",
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
            Field("name", css_class="bg-base-200"),
            Div(
                Button(
                    "cancel",
                    "Annulla",
                    css_class="btn-error btn-sm",
                    onclick="window.modal.close()",
                ),
                Submit(
                    "submit",
                    "Aggiungi",
                    css_class="btn-sm",
                ),
                css_class="mt-4 flex justify-end gap-x-2",
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
            Field("category", css_class="bg-base-200"),
            Field("name", css_class="bg-base-200"),
            Div(
                Button(
                    "cancel",
                    "Annulla",
                    css_class="btn-error btn-sm",
                    onclick="window.modal.close()",
                ),
                Submit(
                    "submit",
                    "Aggiungi",
                    css_class="btn-sm",
                ),
                css_class="mt-4 flex justify-end gap-x-2",
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
                "csv_file",
                css_class="bg-base-200 dark:bg-base-300 file-input file-input-primary w-full",
            ),
            Div(
                Button(
                    "cancel",
                    "Annulla",
                    css_class="btn-error btn-sm",
                    onclick="window.modal.close()",
                ),
                Submit(
                    "submit",
                    "Aggiungi",
                    css_class="btn-sm",
                ),
                css_class="mt-4 flex justify-end gap-x-2",
            ),
        )
