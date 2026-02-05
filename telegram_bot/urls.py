"""URL configuration for telegram_bot app"""

from django.urls import path

from telegram_bot.views import telegram_webhook

app_name = "telegram_bot"

urlpatterns = [
    path("webhook/", telegram_webhook, name="webhook"),
]
