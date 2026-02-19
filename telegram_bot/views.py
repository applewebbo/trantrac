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

from telegram_bot.handlers.auth import (
    handle_contact,
    handle_enrollment_approval,
    handle_start,
)
from telegram_bot.handlers.history import (
    handle_delete_callback,
    handle_recent_transactions,
)
from telegram_bot.handlers.transaction import route_message

logger = logging.getLogger(__name__)

# Shared Application instance — initialized once per worker in ASGI mode,
# preserving context.user_data across requests within the same worker.
_application: Application | None = None


def get_application() -> Application:
    """Get or create the shared Telegram bot Application."""
    global _application
    if _application is None:
        _application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        _application.add_handler(CommandHandler("start", handle_start))
        _application.add_handler(CommandHandler("ultime", handle_recent_transactions))
        _application.add_handler(
            CallbackQueryHandler(
                handle_delete_callback,
                pattern="^(delete:|confirm_delete:|cancel_delete)",
            )
        )
        _application.add_handler(
            CallbackQueryHandler(
                handle_enrollment_approval,
                pattern="^(approve_enrollment:|reject_enrollment:)",
            )
        )
        _application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        _application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, route_message)
        )
    return _application


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
        app = get_application()
        # initialize() is idempotent — safe to call on every request.
        await app.initialize()
        update = Update.de_json(update_data, app.bot)
        await app.process_update(update)
        return JsonResponse({"ok": True})

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request")
        return HttpResponse("Bad request", status=400)

    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return HttpResponse("Internal server error", status=500)
