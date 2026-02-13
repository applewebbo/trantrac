from django.contrib import admin

from .models import (
    BotTransaction,
    CategoryKeyword,
    PendingTransaction,
    TelegramAuthSession,
)


@admin.register(BotTransaction)
class BotTransactionAdmin(admin.ModelAdmin):
    list_display = ["bot_id", "user", "amount", "description", "date", "created_at"]
    list_filter = ["created_at", "user"]
    search_fields = ["bot_id", "description", "user__email"]
    readonly_fields = ["bot_id", "created_at", "telegram_message_id"]


@admin.register(PendingTransaction)
class PendingTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "description",
        "status",
        "retry_count",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["description", "user__email"]
    readonly_fields = ["created_at", "telegram_message_id"]


@admin.register(TelegramAuthSession)
class TelegramAuthSessionAdmin(admin.ModelAdmin):
    list_display = ["chat_id", "phone_number", "created_at", "is_expired"]
    readonly_fields = ["created_at"]

    @admin.display(boolean=True)
    def is_expired(self, obj):
        return obj.is_expired()


@admin.register(CategoryKeyword)
class CategoryKeywordAdmin(admin.ModelAdmin):
    list_display = ["keyword", "subcategory", "priority"]
    list_filter = ["subcategory__category"]
    search_fields = ["keyword", "subcategory__name"]
