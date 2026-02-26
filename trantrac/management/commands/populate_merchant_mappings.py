"""Management command to seed MerchantMapping with common Italian merchants."""

from django.core.management.base import BaseCommand

from trantrac.models import Category, MerchantMapping, Subcategory

# (keyword, category_name, subcategory_name)
MERCHANT_MAPPINGS = [
    # Supermercati
    ("esselunga", "Alimentari", "Supermercato"),
    ("conad", "Alimentari", "Supermercato"),
    ("coop", "Alimentari", "Supermercato"),
    ("eurospin", "Alimentari", "Supermercato"),
    ("lidl", "Alimentari", "Supermercato"),
    ("penny", "Alimentari", "Supermercato"),
    ("carrefour", "Alimentari", "Supermercato"),
    ("auchan", "Alimentari", "Supermercato"),
    ("bennet", "Alimentari", "Supermercato"),
    ("pam", "Alimentari", "Supermercato"),
    ("sigma", "Alimentari", "Supermercato"),
    ("despar", "Alimentari", "Supermercato"),
    ("famila", "Alimentari", "Supermercato"),
    ("aldi", "Alimentari", "Supermercato"),
    ("supermercato", "Alimentari", "Supermercato"),
    # Carburante
    ("eni", "Trasporti", "Carburante"),
    ("agip", "Trasporti", "Carburante"),
    ("q8", "Trasporti", "Carburante"),
    ("shell", "Trasporti", "Carburante"),
    ("api", "Trasporti", "Carburante"),
    ("tamoil", "Trasporti", "Carburante"),
    ("esso", "Trasporti", "Carburante"),
    # Trasporti pubblici / treno
    ("trenitalia", "Trasporti", "Treno"),
    ("italo", "Trasporti", "Treno"),
    # Abbigliamento
    ("zara", "Abbigliamento", "Abbigliamento"),
    ("primark", "Abbigliamento", "Abbigliamento"),
    ("mango", "Abbigliamento", "Abbigliamento"),
    ("uniqlo", "Abbigliamento", "Abbigliamento"),
    # Sport
    ("decathlon", "Sport", "Abbigliamento sportivo"),
    ("intersport", "Sport", "Abbigliamento sportivo"),
    # Casa
    ("ikea", "Casa", "Arredamento"),
    ("leroy", "Casa", "Bricolage"),
    ("brico", "Casa", "Bricolage"),
    # Streaming / intrattenimento
    ("netflix", "Intrattenimento", "Streaming"),
    ("spotify", "Intrattenimento", "Streaming"),
    ("disney", "Intrattenimento", "Streaming"),
    # Farmacia / salute
    ("farmacia", "Salute", "Farmacia"),
    # Utenze
    ("enel", "Utenze", "Luce e gas"),
]


class Command(BaseCommand):
    help = "Seed MerchantMapping with common Italian merchants (idempotent)."

    def handle(self, *args, **options):
        created_count = 0
        for keyword, category_name, subcategory_name in MERCHANT_MAPPINGS:
            category, _ = Category.objects.get_or_create(name=category_name)
            subcategory, _ = Subcategory.objects.get_or_create(
                name=subcategory_name,
                category=category,
                defaults={"skip_sheet_save": True},
            )
            _, created = MerchantMapping.objects.get_or_create(
                keyword=keyword,
                defaults={"category": category, "subcategory": subcategory},
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Done. {created_count} new merchant mappings created.")
        )
