import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import reverse

User = get_user_model()


class Command(BaseCommand):
    help = "Send monthly reminder to admin users to import bank transactions"

    def handle(self, *args, **options):
        # Get all admin/staff users
        admin_users = User.objects.filter(is_staff=True) | User.objects.filter(
            is_superuser=True
        )
        admin_users = admin_users.distinct()

        if not admin_users.exists():
            self.stdout.write(
                self.style.WARNING("No admin users found. Email not sent.")
            )
            return

        # Prepare email content
        subject = "Reminder: Import transazioni bancarie"

        # Build upload URL if SITE_URL is configured
        upload_path = reverse("upload_csv")
        site_url = os.getenv("SITE_URL", "").rstrip("/")

        if site_url:
            upload_url = f"{site_url}{upload_path}"
            message = f"""
Ciao,

Questo è un promemoria mensile per ricordarti di importare le transazioni bancarie.

Accedi alla pagina di upload CSV per aggiungere le nuove transazioni del mese:
{upload_url}

Grazie,
TranTrac
            """.strip()
        else:
            message = """
Ciao,

Questo è un promemoria mensile per ricordarti di importare le transazioni bancarie.

Accedi all'applicazione e vai alla pagina di upload CSV per aggiungere le nuove transazioni del mese.

Grazie,
TranTrac
            """.strip()

        # Send email to each admin user
        sent_count = 0
        failed_count = 0

        for user in admin_users:
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f"Email sent to {user.email}"))
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"Failed to send email to {user.email}: {str(e)}")
                )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {sent_count} emails sent, {failed_count} failed"
            )
        )
