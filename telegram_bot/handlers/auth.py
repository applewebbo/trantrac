"""Authentication handlers for Telegram bot"""

import logging

from asgiref.sync import sync_to_async
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes

from telegram_bot.models import TelegramAuthSession
from users.models import User

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.

    - Approved user: show role-specific welcome message
    - Pending user: show awaiting approval message
    - New user: request phone number sharing
    """
    logger.info(f"Received /start command from chat_id: {update.effective_chat.id}")
    chat_id = update.effective_chat.id

    user = await sync_to_async(User.objects.filter(telegram_chat_id=chat_id).first)()

    if user and user.telegram_status == User.TELEGRAM_STATUS_APPROVED:
        if user.is_staff:
            await update.message.reply_text(
                f"👋 Ciao {user.display_name or user.email}! Sei admin.\n\n"
                "Comandi disponibili:\n"
                "• Invia *IMPORTO/DESCRIZIONE* per registrare una spesa\n"
                "• /ultime — ultime transazioni inserite\n"
                "• Invia un file *.csv* per importare le transazioni\n",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"👋 Ciao {user.display_name or user.email}!\n\n"
                "Sei già collegato. Invia una transazione nel formato:\n"
                "*IMPORTO/DESCRIZIONE*\n\n"
                "Esempio: `50/caffè al bar`",
                parse_mode="Markdown",
            )
        return

    if user and user.telegram_status == User.TELEGRAM_STATUS_PENDING:
        await update.message.reply_text(
            "⏳ La tua richiesta è in attesa di approvazione da parte dell'admin.\n"
            "Ti notificherò appena confermata."
        )
        return

    # Request phone number
    keyboard = [
        [{"text": "📱 Condividi il tuo numero", "request_contact": True}],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    await update.message.reply_text(
        "👋 Benvenuto su TranTrac Bot!\n\n"
        "Per iniziare, condividi il tuo numero di telefono.\n"
        "Useremo questo numero per collegare il tuo account.",
        reply_markup=reply_markup,
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle phone number sharing.

    Creates auth session and requests email.
    """
    chat_id = update.effective_chat.id
    contact = update.message.contact

    if not contact or not contact.phone_number:
        await update.message.reply_text(
            "❌ Numero di telefono non valido. Riprova con /start",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    phone_number = contact.phone_number

    # Create or update auth session
    await sync_to_async(TelegramAuthSession.objects.update_or_create)(
        chat_id=chat_id,
        defaults={"phone_number": phone_number},
    )

    await update.message.reply_text(
        "✅ Numero ricevuto!\n\n"
        "Ora invia la tua *email* registrata su TranTrac.\n"
        "Esempio: `tuo@email.com`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )


async def handle_email_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle email message during auth flow.

    Links Telegram account to User if email matches, then:
    - Staff users: auto-approved
    - Regular users: pending admin approval
    """
    chat_id = update.effective_chat.id
    email = update.message.text.strip()

    # Check if there's a pending auth session
    session = await sync_to_async(
        TelegramAuthSession.objects.filter(chat_id=chat_id).first
    )()

    if not session:
        await update.message.reply_text(
            "❌ Sessione di autenticazione non trovata.\nRiprova con /start"
        )
        return

    # Check if session expired
    if await sync_to_async(session.is_expired)():
        await sync_to_async(session.delete)()
        await update.message.reply_text(
            "⏰ Sessione scaduta (5 minuti).\nRiprova con /start"
        )
        return

    # Find user by email
    user = await sync_to_async(User.objects.filter(email__iexact=email).first)()

    if not user:
        await update.message.reply_text(
            "❌ Email non trovata nel sistema.\n\n"
            "Verifica di aver inserito l'email corretta registrata su TranTrac.\n"
            "Altrimenti riprova con /start"
        )
        return

    # Check if another user already linked to this chat
    other_user_exists = await sync_to_async(
        User.objects.filter(telegram_chat_id=chat_id).exclude(id=user.id).exists
    )()

    if other_user_exists:
        await update.message.reply_text(
            "❌ Questo account Telegram è già collegato a un altro utente."
        )
        return

    # Handle already enrolled users
    if user.telegram_chat_id == chat_id:
        if user.telegram_status == User.TELEGRAM_STATUS_APPROVED:
            await update.message.reply_text(
                "✅ Sei già collegato e approvato.\nUsa /start per vedere i comandi disponibili."
            )
            await sync_to_async(session.delete)()
            return
        if user.telegram_status == User.TELEGRAM_STATUS_PENDING:
            await update.message.reply_text(
                "⏳ La tua richiesta è già in attesa di approvazione.\n"
                "Ti notificherò appena confermata."
            )
            await sync_to_async(session.delete)()
            return

    # Link user to Telegram
    user.telegram_chat_id = chat_id
    user.phone_number = session.phone_number

    if user.is_staff:
        user.telegram_status = User.TELEGRAM_STATUS_APPROVED
        await sync_to_async(user.save)()
        await sync_to_async(session.delete)()
        await update.message.reply_text(
            f"✅ Account admin collegato!\n\n"
            f"👤 {user.display_name or user.email}\n\n"
            "Comandi disponibili:\n"
            "• Invia *IMPORTO/DESCRIZIONE* per registrare una spesa\n"
            "• /ultime — ultime transazioni inserite\n"
            "• Invia un file *.csv* per importare le transazioni\n",
            parse_mode="Markdown",
        )
    else:
        user.telegram_status = User.TELEGRAM_STATUS_PENDING
        await sync_to_async(user.save)()
        await sync_to_async(session.delete)()
        await _notify_admins_of_enrollment(context, user)
        await update.message.reply_text(
            f"✅ Account trovato!\n\n"
            f"👤 {user.display_name or user.email}\n\n"
            "⏳ La tua richiesta è in attesa di approvazione da parte dell'admin.\n"
            "Ti notificherò appena confermata."
        )


async def _notify_admins_of_enrollment(
    context: ContextTypes.DEFAULT_TYPE, user: User
) -> None:
    """Send enrollment approval request to all active admin users."""
    admins = await sync_to_async(
        lambda: list(
            User.objects.filter(
                is_staff=True,
                telegram_chat_id__isnull=False,
                telegram_status=User.TELEGRAM_STATUS_APPROVED,
            )
        )
    )()

    if not admins:
        logger.warning(
            f"No active admin found to approve enrollment for user {user.email}"
        )
        return

    name = user.display_name or user.email
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Approva", callback_data=f"approve_enrollment:{user.id}"
                ),
                InlineKeyboardButton(
                    "❌ Rifiuta", callback_data=f"reject_enrollment:{user.id}"
                ),
            ]
        ]
    )

    for admin in admins:
        await context.bot.send_message(
            chat_id=admin.telegram_chat_id,
            text=(
                f"🔐 Nuova richiesta di accesso al bot:\n\n"
                f"👤 {name}\n"
                f"📧 {user.email}\n"
                f"📱 {user.phone_number}"
            ),
            reply_markup=keyboard,
        )


async def handle_enrollment_approval(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle admin approval/rejection of enrollment requests.

    Callback data:
    - approve_enrollment:{user_id}
    - reject_enrollment:{user_id}
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    action, user_id_str = data.split(":", 1)
    user_id = int(user_id_str)

    pending_user = await sync_to_async(User.objects.filter(id=user_id).first)()

    if not pending_user:
        await query.edit_message_text("❌ Utente non trovato.")
        return

    name = pending_user.display_name or pending_user.email

    if action == "approve_enrollment":
        pending_user.telegram_status = User.TELEGRAM_STATUS_APPROVED
        await sync_to_async(pending_user.save)()

        await query.edit_message_text(f"✅ Approvato: {name}")

        if pending_user.telegram_chat_id:
            await context.bot.send_message(
                chat_id=pending_user.telegram_chat_id,
                text=(
                    "✅ La tua richiesta è stata approvata!\n\n"
                    "Ora puoi usare il bot. Invia una transazione nel formato:\n"
                    "*IMPORTO/DESCRIZIONE*\n\n"
                    "Esempio: `50/caffè al bar`"
                ),
                parse_mode="Markdown",
            )

    elif action == "reject_enrollment":
        if pending_user.telegram_chat_id:
            await context.bot.send_message(
                chat_id=pending_user.telegram_chat_id,
                text=(
                    "❌ La tua richiesta di accesso al bot è stata rifiutata.\n"
                    "Contatta l'amministratore per maggiori informazioni."
                ),
            )

        pending_user.telegram_chat_id = None
        pending_user.telegram_status = None
        pending_user.phone_number = ""
        await sync_to_async(pending_user.save)()

        await query.edit_message_text(f"❌ Rifiutato: {name}")
