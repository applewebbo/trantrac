"""Authentication handlers for Telegram bot"""

import logging

from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from telegram_bot.models import TelegramAuthSession
from users.models import User

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command

    - If user is authenticated: show welcome message
    - If not: request phone number sharing
    """
    logger.info(f"Received /start command from chat_id: {update.effective_chat.id}")
    chat_id = update.effective_chat.id

    # Check if user is already authenticated
    user = await sync_to_async(User.objects.filter(telegram_chat_id=chat_id).first)()
    if user:
        await update.message.reply_text(
            f"👋 Ciao {user.display_name or user.email}!\n\n"
            "Sei già collegato. Invia una transazione nel formato:\n"
            "*IMPORTO/DESCRIZIONE*\n\n"
            "Esempio: `50/caffè al bar`",
            parse_mode="Markdown",
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
    Handle phone number sharing

    Creates auth session and requests email
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
    session, created = await sync_to_async(
        TelegramAuthSession.objects.update_or_create
    )(
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
    Handle email message during auth flow

    Links Telegram account to User if email matches
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

    # Link user to Telegram
    user.telegram_chat_id = chat_id
    user.phone_number = session.phone_number
    await sync_to_async(user.save)()

    # Delete auth session
    await sync_to_async(session.delete)()

    await update.message.reply_text(
        f"✅ Account collegato con successo!\n\n"
        f"👤 {user.display_name or user.email}\n\n"
        "Ora puoi inviare transazioni nel formato:\n"
        "*IMPORTO/DESCRIZIONE*\n\n"
        "Esempio: `50/caffè al bar`",
        parse_mode="Markdown",
    )
