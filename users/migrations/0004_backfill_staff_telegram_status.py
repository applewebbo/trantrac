"""
Data migration: set telegram_status='approved' for staff users with telegram_chat_id set.

Fixes the case where admin users enrolled via bot before the telegram_status field
was introduced, leaving their status as NULL and preventing enrollment notifications.
"""

from django.db import migrations


def backfill_staff_telegram_status(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(
        is_staff=True,
        telegram_chat_id__isnull=False,
        telegram_status__isnull=True,
    ).update(telegram_status="approved")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_user_telegram_status"),
    ]

    operations = [
        migrations.RunPython(
            backfill_staff_telegram_status,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
