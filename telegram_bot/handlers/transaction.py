"""Transaction handlers for Telegram bot"""

from asgiref.sync import sync_to_async
from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.models import TelegramAuthSession
from telegram_bot.services.parser import parse_transaction_message
from telegram_bot.services.suggestions import get_subcategory_suggestions
from telegram_bot.services.transaction_service import create_transaction
from trantrac.models import Subcategory
from users.models import User


async def route_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main router for incoming messages

    Handles:
    - Transaction messages (AMOUNT/DESCRIPTION)
    - Subcategory selection (number)
    - Confirmation (s/n)
    - Navigation (n/p for pagination)
    """
    chat_id = update.effective_chat.id
    message_text = update.message.text.strip()

    # Check authentication
    user = await sync_to_async(User.objects.filter(telegram_chat_id=chat_id).first)()

    if not user:
        # Check if in auth flow
        session_exists = await sync_to_async(
            TelegramAuthSession.objects.filter(chat_id=chat_id).exists
        )()

        if session_exists:
            # Handle as email message
            from telegram_bot.handlers.auth import handle_email_message

            await handle_email_message(update, context)
            return

        # Not authenticated
        await update.message.reply_text(
            "❌ Account non collegato.\nUsa /start per collegare il tuo account."
        )
        return

    # Get user's pending state from context
    user_data = context.user_data
    awaiting_subcategory = user_data.get("awaiting_subcategory", False)
    awaiting_confirmation = user_data.get("awaiting_confirmation", False)
    user_data.get("current_page", 0)

    # Handle confirmation (s/n)
    if awaiting_confirmation:
        await handle_final_confirmation(update, context, user, message_text)
        return

    # Handle subcategory selection (number)
    if awaiting_subcategory:
        await handle_subcategory_selection(update, context, user, message_text)
        return

    # Handle new transaction message
    parsed = parse_transaction_message(message_text)
    if parsed:
        await handle_transaction_message(update, context, user, parsed)
    else:
        await update.message.reply_text(
            "❌ Formato non valido.\n\n"
            "Usa il formato: *IMPORTO/DESCRIZIONE*\n"
            "Esempio: `50/caffè al bar`",
            parse_mode="Markdown",
        )


async def handle_transaction_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user,
    parsed: dict,
) -> None:
    """
    Handle new transaction message

    Shows subcategory suggestions
    """
    amount = parsed["amount"]
    description = parsed["description"]

    # Get suggestions
    suggestions = await sync_to_async(get_subcategory_suggestions)(
        user, description, limit=5
    )

    if not suggestions:
        await update.message.reply_text(
            "❌ Nessuna sottocategoria disponibile.\n"
            "Contatta l'amministratore per configurare le categorie."
        )
        return

    # Store pending transaction in context
    context.user_data["pending_transaction"] = {
        "amount": amount,
        "description": description,
        "suggestions": [s.id for s in suggestions],
        "message_id": update.message.message_id,
    }
    context.user_data["awaiting_subcategory"] = True
    context.user_data["current_page"] = 0

    # Format suggestion list
    message_lines = [
        f"💰 *{amount}€* - {description}\n",
        "Scegli sottocategoria:\n",
    ]

    for idx, subcat in enumerate(suggestions, start=1):
        message_lines.append(f"{idx}. {subcat.category.name} > *{subcat.name}*")

    message_lines.append("\n0. Altro... (mostra tutte)")

    await update.message.reply_text(
        "\n".join(message_lines),
        parse_mode="Markdown",
    )


async def handle_subcategory_selection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user,
    message_text: str,
) -> None:
    """
    Handle subcategory selection (number input)
    """
    pending = context.user_data.get("pending_transaction")
    if not pending:
        await update.message.reply_text("❌ Nessuna transazione in attesa.")
        return

    # Try to parse as number
    try:
        choice = int(message_text)
    except ValueError:
        await update.message.reply_text(
            "❌ Inserisci un numero dalla lista.\nOppure annulla con /start"
        )
        return

    # Handle "0. Altro..."
    if choice == 0:
        await show_all_subcategories(update, context, user, page=0)
        return

    # Validate choice
    suggestions_ids = pending["suggestions"]
    if choice < 1 or choice > len(suggestions_ids):
        await update.message.reply_text(
            f"❌ Numero non valido. Scegli da 1 a {len(suggestions_ids)}, o 0 per vedere tutte."
        )
        return

    # Get selected subcategory
    selected_id = suggestions_ids[choice - 1]
    subcategory = await sync_to_async(
        Subcategory.objects.filter(id=selected_id).first
    )()

    if not subcategory:
        await update.message.reply_text("❌ Sottocategoria non trovata.")
        return

    # Store selection and request confirmation
    pending["selected_subcategory_id"] = subcategory.id
    context.user_data["awaiting_subcategory"] = False
    context.user_data["awaiting_confirmation"] = True

    await update.message.reply_text(
        f"📊 *{subcategory.category.name}* > {subcategory.name}\n"
        f"💰 {pending['amount']}€ - {pending['description']}\n\n"
        "Conferma? (s/n)",
        parse_mode="Markdown",
    )


async def show_all_subcategories(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user,
    page: int = 0,
) -> None:
    """
    Show paginated list of all subcategories

    Each page shows 10 items + navigation
    """
    PAGE_SIZE = 10

    all_subcategories = await sync_to_async(
        lambda: list(Subcategory.objects.select_related("category").all())
    )()
    total_pages = (len(all_subcategories) + PAGE_SIZE - 1) // PAGE_SIZE

    if page < 0 or page >= total_pages:
        page = 0

    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_items = all_subcategories[start_idx:end_idx]

    # Update stored suggestions with ALL subcategories
    context.user_data["pending_transaction"]["suggestions"] = [
        s.id for s in all_subcategories
    ]
    context.user_data["current_page"] = page

    # Format message
    message_lines = ["📋 *Tutte le sottocategorie:*\n"]

    for idx, subcat in enumerate(page_items, start=start_idx + 1):
        message_lines.append(f"{idx}. {subcat.category.name} > *{subcat.name}*")

    # Navigation
    nav_parts = []
    if page > 0:
        nav_parts.append("⬅️ Precedente: *p*")
    if page < total_pages - 1:
        nav_parts.append("Successiva: *n* ➡️")

    if nav_parts:
        message_lines.append("\n" + " | ".join(nav_parts))

    message_lines.append(f"\nPagina {page + 1}/{total_pages}")

    await update.message.reply_text(
        "\n".join(message_lines),
        parse_mode="Markdown",
    )


async def handle_final_confirmation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user,
    message_text: str,
) -> None:
    """
    Handle final confirmation (s/n)
    """
    pending = context.user_data.get("pending_transaction")
    if not pending:
        await update.message.reply_text("❌ Nessuna transazione in attesa.")
        return

    confirmation = message_text.lower()

    if confirmation == "n":
        # Cancel
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Transazione annullata.\n\nInvia un nuovo messaggio per ricominciare."
        )
        return

    if confirmation != "s":
        await update.message.reply_text(
            "❌ Risposta non valida.\nRispondi *s* per confermare o *n* per annullare.",
            parse_mode="Markdown",
        )
        return

    # Confirm and save
    subcategory = await sync_to_async(
        Subcategory.objects.filter(id=pending["selected_subcategory_id"]).first
    )()

    if not subcategory:
        await update.message.reply_text("❌ Sottocategoria non trovata.")
        context.user_data.clear()
        return

    success, message = await sync_to_async(create_transaction)(
        user=user,
        amount=pending["amount"],
        description=pending["description"],
        subcategory=subcategory,
        telegram_message_id=pending["message_id"],
    )

    await update.message.reply_text(message)

    # Clear context
    context.user_data.clear()
