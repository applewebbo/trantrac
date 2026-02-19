from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    display_name = models.CharField(max_length=50, blank=True)
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID chat Telegram per bot",
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Numero di telefono per autenticazione Telegram",
    )

    TELEGRAM_STATUS_PENDING = "pending"
    TELEGRAM_STATUS_APPROVED = "approved"
    TELEGRAM_STATUS_CHOICES = [
        (TELEGRAM_STATUS_PENDING, "In attesa di approvazione"),
        (TELEGRAM_STATUS_APPROVED, "Approvato"),
    ]
    telegram_status = models.CharField(
        max_length=20,
        choices=TELEGRAM_STATUS_CHOICES,
        null=True,
        blank=True,
        help_text="Stato approvazione enrollment Telegram (NULL = non enrollato)",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
