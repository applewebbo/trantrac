from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_bot_id():
    return "BOT-" + uuid4().hex[:8].upper()


class BotTransaction(models.Model):
    """Transazioni salvate con successo via bot (max 5 per utente)"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    category = models.ForeignKey("trantrac.Category", on_delete=models.CASCADE)
    subcategory = models.ForeignKey("trantrac.Subcategory", on_delete=models.CASCADE)
    account = models.ForeignKey("trantrac.Account", on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    telegram_message_id = models.BigIntegerField()
    bot_id = models.CharField(max_length=20, unique=True, default=generate_bot_id)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["bot_id"]),
        ]

    def __str__(self):
        return f"{self.bot_id} — {self.user} — {self.amount}€ — {self.description}"


class PendingTransaction(models.Model):
    """Transazioni fallite da ritentare"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200)
    category = models.ForeignKey("trantrac.Category", on_delete=models.CASCADE)
    subcategory = models.ForeignKey("trantrac.Subcategory", on_delete=models.CASCADE)
    account = models.ForeignKey("trantrac.Account", on_delete=models.CASCADE)
    date = models.DateField()

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    retry_count = models.IntegerField(default=0)
    last_error = models.TextField(blank=True)
    telegram_message_id = models.BigIntegerField()

    STATUS_CHOICES = [
        ("pending", "In attesa"),
        ("processing", "In elaborazione"),
        ("completed", "Completata"),
        ("failed", "Fallita"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.amount}€ - {self.status}"


class TelegramAuthSession(models.Model):
    """Sessione temporanea per autenticazione via numero telefono"""

    chat_id = models.BigIntegerField(unique=True)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["chat_id"])]

    def is_expired(self) -> bool:
        """Sessione scade dopo 5 minuti"""
        expiry_time = self.created_at + timedelta(minutes=5)
        return timezone.now() > expiry_time

    def __str__(self):
        return f"Chat {self.chat_id} - {self.phone_number}"


class CategoryKeyword(models.Model):
    """Parole chiave per auto-categorizzazione"""

    keyword = models.CharField(max_length=100, db_index=True)
    subcategory = models.ForeignKey("trantrac.Subcategory", on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)

    class Meta:
        unique_together = [("keyword", "subcategory")]
        ordering = ["-priority", "keyword"]

    def __str__(self):
        return f"{self.keyword} → {self.subcategory.name}"
