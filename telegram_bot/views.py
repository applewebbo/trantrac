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


def _build_application() -> Application:
    """Build a fresh Telegram bot application with all handlers registered."""
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("ultime", handle_recent_transactions))
    app.add_handler(
        CallbackQueryHandler(
            handle_delete_callback,
            pattern="^(delete:|confirm_delete:|cancel_delete)",
        )
    )
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_message))
    return app


@csrf_exempt
async def telegram_webhook(request: HttpRequest) -> HttpResponse:
    """Webhook endpoint for Telegram updates."""
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret token")
        return HttpResponse("Unauthorized", status=401)

    try:
        update_data = json.loads(request.body)

        # Use async context manager so the HTTP client lifecycle (init + shutdown)
        # stays within the same event loop as the request — avoids "Event loop is closed"
        # errors with Granian/uvloop on Python 3.14.
        async with _build_application() as app:
            update = Update.de_json(update_data, app.bot)
            await app.process_update(update)

        return JsonResponse({"ok": True})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request")
        return HttpResponse("Bad request", status=400)

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return HttpResponse("Internal server error", status=500)
