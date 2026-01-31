from datetime import datetime, timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Button, Div, Field, Layout, Submit
from django import forms
from django.urls import reverse_lazy

from trantrac.models import Account, Category, Subcategory

HTML_ADD_BUTTON = """
    <button hx-get="{% url 'add_category' %}"
            hx-target="#modal-content"
            hx-swap="innerHTML"
            onclick="window.modal.showModal()"
            class='btn btn-sm btn-primary'>
        {% heroicon_mini 'plus' %}
    </button>
    """
HTML_ADD_SUBCATEGORY_BUTTON = """
    <button class='btn btn-sm btn-primary'
            x-bind:class="{ 'btn-disabled': !hasCategory }"
            hx-get="{% url 'add_subcategory' %}"
            hx-target="#modal-content"
            hx-swap="innerHTML"
            @click="$el.setAttribute('hx-vals', JSON.stringify({category: $refs.categorySelect.value}))"
            onclick="window.modal.showModal()">
        {% heroicon_mini 'plus' %}
    </button>
"""

HTML_QUICK_CATEGORIES_START = """
<!-- Quick Categories Section -->
<div class="mb-4 rounded-lg border-2 border-gray-100 dark:border-base-300  dark:bg-base-300 p-4"
     x-data="{
         activeTab: ({{ has_category_data|yesno:'true,false' }}) ? 'recent' : 'all',
         selectCategory(categoryId, subcategoryId) {
             const categorySelect = document.getElementById('id_category');
             const subcategorySelect = document.getElementById('id_subcategory');

             categorySelect.value = categoryId;
             categorySelect.dispatchEvent(new Event('change'));

             setTimeout(() => {
                 subcategorySelect.value = subcategoryId;
             }, 200);
         }
     }">
    <!-- DaisyUI Tabs -->
    <div role="tablist" class="tabs tabs-border">
        <a role="tab"
           class="tab"
           :class="{ 'tab-active': activeTab === 'recent' }"
           @click="activeTab = 'recent'">
            Recenti
        </a>
        <a role="tab"
           class="tab"
           :class="{ 'tab-active': activeTab === 'most-used' }"
           @click="activeTab = 'most-used'">
            Più usate
        </a>
        <a role="tab"
           class="tab"
           :class="{ 'tab-active': activeTab === 'all' }"
           @click="activeTab = 'all'">
            Scegli la categoria
        </a>
    </div>

    <!-- Tab Content -->
    <div class="mt-4">
        <!-- Recent Categories -->
        <div x-show="activeTab === 'recent'" class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {% for item in recent_categories %}
            <button type="button"
                    class="btn btn-sm btn-primary"
                    @click="selectCategory({{ item.category }}, {{ item.subcategory }})">
                {{ item.subcategory__name }}
            </button>
            {% empty %}
            <p class="col-span-full text-sm text-gray-500">Nessuna categoria recente</p>
            {% endfor %}
        </div>

        <!-- Most Used Categories -->
        <div x-show="activeTab === 'most-used'" class="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {% for item in most_used_categories %}
            <button type="button"
                    class="btn btn-sm btn-primary"
                    @click="selectCategory({{ item.category }}, {{ item.subcategory }})">
                {{ item.subcategory__name }}
            </button>
            {% empty %}
            <p class="col-span-full text-sm text-gray-500">Nessuna categoria usata</p>
            {% endfor %}
        </div>

        <!-- All Categories (Standard Form) -->
        <div x-show="activeTab === 'all'">
"""

HTML_QUICK_CATEGORIES_END = """
        </div>
    </div>
</div>
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
            except (ValueError, TypeError):
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
                            <label class="flex items-center gap-2 bg-base-200 dark:bg-base-300 border border-base-300 rounded-lg py-2 px-4">
                                <input type="number" step="0.01" name="amount" id="id_amount"
                                       class="grow bg-transparent focus:outline-none text-base-content" placeholder="0.00" required />
                                {% heroicon_outline 'currency-euro' class='w-6 h-6 text-base-content' %}
                            </label>
                        """),
                        css_class="grow",
                    ),
                    Field(
                        "date",
                        css_class="bg-base-200 dark:bg-base-300",
                        wrapper_class="grow",
                    ),
                    css_class="flex flex-col md:flex-row gap-3 mb-3",
                ),
                Field("description", css_class="bg-base-200 dark:bg-base-300"),
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
                    hx_vals='js:{"category": event.target.value}',
                ),
                Div(
                    Field(
                        "subcategory",
                        css_class="bg-base-200 dark:bg-base-300",
                        **{"x-bind:disabled": "!hasCategory"},
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
            Field("name", css_class="bg-base-200 dark:bg-base-300"),
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
            Field("category", css_class="bg-base-200 dark:bg-base-300"),
            Field("name", css_class="bg-base-200 dark:bg-base-300"),
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
