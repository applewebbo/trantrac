"""Webhook view for Telegram bot"""

import json
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from telegram_bot.handlers.auth import handle_contact, handle_start
from telegram_bot.handlers.history import (
    handle_delete_callback,
    handle_recent_transactions,
)
from telegram_bot.handlers.transaction import route_message

logger = logging.getLogger(__name__)

# Initialize bot application (cached)
_application = None


def get_application() -> Application:
    """Get or create Telegram bot application"""
    global _application
    if _application is None:
        _application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Register handlers
        _application.add_handler(CommandHandler("start", handle_start))
        _application.add_handler(CommandHandler("ultimi", handle_recent_transactions))
        _application.add_handler(
            CallbackQueryHandler(
                handle_delete_callback,
                pattern="^(delete:|confirm_delete:|cancel_delete)",
            )
        )
        _application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        _application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, route_message)
        )

    return _application


@csrf_exempt
async def telegram_webhook(request: HttpRequest) -> HttpResponse:
    """
    Webhook endpoint for Telegram updates

    Verifies secret token and processes updates
    """
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    # Verify secret token (optional but recommended)
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret token")
        return HttpResponse("Unauthorized", status=401)

    try:
        # Parse update
        update_data = json.loads(request.body)
        update = Update.de_json(update_data, get_application().bot)

        # Process update
        app = get_application()
        await app.initialize()
        await app.process_update(update)

        return JsonResponse({"ok": True})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request")
        return HttpResponse("Bad request", status=400)

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return HttpResponse("Internal server error", status=500)
