# Telegram Bot Setup & Configuration

This guide covers the complete setup process for the TranTrac Telegram Bot, from creation with BotFather to production deployment.

## Table of Contents

1. [Creating the Bot](#creating-the-bot)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Bot Commands](#bot-commands)
5. [Troubleshooting](#troubleshooting)

---

## Creating the Bot

### Step 1: Create Bot with BotFather

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Start a chat and send `/newbot`
3. Follow the prompts:
   - **Bot name**: `TranTrac Bot` (or your preferred display name)
   - **Bot username**: Must end in `bot` (e.g., `trantrac_finance_bot`)
4. **Save the bot token** - you'll need it for configuration

Example output:
```
Done! Congratulations on your new bot. You will find it at t.me/trantrac_finance_bot.
You can now add a description, about section and profile picture for your bot.

Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
Keep your token secure and store it safely, it can be used by anyone to control your bot.
```

### Step 2: Configure Bot Settings

Configure your bot with BotFather:

```
/setdescription
→ Select your bot
→ Enter: "TranTrac bot for quick expense tracking. Send transactions in format: AMOUNT/DESCRIPTION"

/setabouttext
→ Select your bot
→ Enter: "Family finance tracker with Google Sheets integration"

/setcommands
→ Select your bot
→ Enter:
start - Start using the bot
help - Show help message
```

### Step 3: Optional - Set Bot Picture

1. Create or choose a bot profile picture (recommended: 512x512px)
2. Send `/setuserpic` to BotFather
3. Select your bot and upload the image

---

## Local Development Setup

### Prerequisites

- Python 3.13+
- uv (Python package manager)
- Telegram bot token from BotFather

### Configuration

1. **Add token to `.env`**:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=  # Leave empty for polling mode
TELEGRAM_WEBHOOK_SECRET=  # Leave empty for polling mode
```

2. **Run database migrations** (if not already done):

```bash
python manage.py migrate
```

3. **Create categories and subcategories** via Django admin or web interface

### Running the Bot (Development)

Use polling mode for local development:

```bash
python manage.py runbot
```

The bot will start and listen for messages. You should see:
```
Starting bot in polling mode...
Bot started! Press Ctrl+C to stop.
```

### Testing the Bot

1. **Start the bot**: Open Telegram and search for your bot username
2. **Send `/start`**: The bot will request your phone number
3. **Share contact**: Use the "Share Contact" button
4. **Enter email**: Send your registered email address
5. **Send transaction**: Try `50/caffè` (amount/description)
6. **Select category**: Choose from suggested subcategories
7. **Confirm**: Reply `s` (sì) to save to Google Sheets

---

## Production Deployment

### Prerequisites

- Deployed Django application with HTTPS
- Public URL for webhook endpoint
- Telegram bot token

### Step 1: Environment Configuration

Add to your production `.env`:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/telegram/webhook/
TELEGRAM_WEBHOOK_SECRET=your_random_secret_here  # Generate with: openssl rand -hex 32

# Site URL (required for webhook)
SITE_URL=https://yourdomain.com
```

**Security Note**: Keep `TELEGRAM_WEBHOOK_SECRET` secure. It validates incoming webhook requests.

### Step 2: Deploy Application

1. **Deploy your code** with the updated environment variables
2. **Run migrations**:

```bash
python manage.py migrate
```

3. **Collect static files** (if needed):

```bash
python manage.py collectstatic --noinput
```

### Step 3: Set Webhook

After deployment, configure the webhook:

```bash
python manage.py setwebhook
```

Expected output:
```
Setting webhook for bot...
Webhook URL: https://yourdomain.com/telegram/webhook/
✓ Webhook set successfully
✓ Webhook info:
  URL: https://yourdomain.com/telegram/webhook/
  Pending updates: 0
```

### Step 4: Verify Webhook

Check webhook status:

```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

Should return:
```json
{
  "ok": true,
  "result": {
    "url": "https://yourdomain.com/telegram/webhook/",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

### Step 5: Setup Cronjobs

Add these cronjobs for maintenance tasks:

```cron
# Retry failed Google Sheets transactions (every 15 minutes)
*/15 * * * * cd /path/to/trantrac && /path/to/.venv/bin/python manage.py retry_pending_transactions

# Cleanup expired auth sessions (every hour)
0 * * * * cd /path/to/trantrac && /path/to/.venv/bin/python manage.py cleanup_auth_sessions
```

---

## Bot Commands

### User Commands

- `/start` - Begin authentication flow or restart
- `/help` - Show help message with usage instructions

### Transaction Format

Send messages in format: `AMOUNT/DESCRIPTION`

Examples:
- `50/caffè` - €50.00 for coffee
- `125.50/spesa settimanale` - €125.50 for weekly shopping
- `30€/pizza` - €30.00 for pizza (currency symbols are removed)

### Workflow

1. **Send transaction** → Bot parses amount and description
2. **View suggestions** → Bot shows top 5 relevant subcategories
3. **Select number** → Choose subcategory (or `0` for full list)
4. **Navigate** (if needed) → Use `n` (next) or `p` (previous) for pagination
5. **Confirm** → Reply `s` (sì) to save, `n` (no) to cancel

---

## Troubleshooting

### Bot Not Responding

**Polling Mode (Development)**:
1. Check if `runbot` command is running
2. Verify `TELEGRAM_BOT_TOKEN` is correct
3. Check console for errors

**Webhook Mode (Production)**:
1. Verify webhook is set: `curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
2. Check webhook URL is publicly accessible with HTTPS
3. Verify `TELEGRAM_WEBHOOK_SECRET` matches between `.env` and webhook setup
4. Check application logs for errors

### Authentication Issues

**"Email not found" error**:
- Ensure user is registered in Django admin or web interface
- Email must match exactly (case-insensitive)

**Phone number not accepted**:
- Use Telegram's "Share Contact" button (not manual typing)
- Ensure phone number format is international (e.g., +39...)

### Google Sheets Errors

**"⚠️ Errore nel salvataggio su Google Sheets"**:
- Transaction is saved to `PendingTransaction` model
- Will be retried automatically by cronjob
- Check Google Sheets API credentials in `.env`
- Verify service account has write access to spreadsheet

**Manually retry failed transactions**:
```bash
python manage.py retry_pending_transactions
```

### Webhook Errors

**"Invalid webhook secret" (401 Unauthorized)**:
- Telegram sends `X-Telegram-Bot-Api-Secret-Token` header
- Must match `TELEGRAM_WEBHOOK_SECRET` in `.env`
- Regenerate secret if compromised: `openssl rand -hex 32`

**Webhook not receiving updates**:
1. Check HTTPS certificate is valid
2. Verify webhook URL is publicly accessible
3. Check firewall/security group settings
4. Test endpoint manually: `curl -X POST https://yourdomain.com/telegram/webhook/`

### Management Commands

**List all available bot commands**:
```bash
python manage.py help | grep -E "(runbot|setwebhook|retry|cleanup)"
```

**Check pending transactions**:
```bash
python manage.py shell
>>> from telegram_bot.models import PendingTransaction
>>> PendingTransaction.objects.filter(synced=False).count()
```

**Clear expired auth sessions manually**:
```bash
python manage.py cleanup_auth_sessions
```

---

## Security Best Practices

1. **Keep token secure**: Never commit `TELEGRAM_BOT_TOKEN` to version control
2. **Use webhook secret**: Always set `TELEGRAM_WEBHOOK_SECRET` in production
3. **HTTPS only**: Telegram requires HTTPS for webhooks (no self-signed certs)
4. **Validate users**: Only registered users can use the bot (email verification)
5. **Rate limiting**: Consider adding rate limiting to webhook endpoint
6. **Monitor logs**: Watch for suspicious activity or repeated failures

---

## Additional Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [python-telegram-bot Library](https://docs.python-telegram-bot.org/)
- [BotFather Commands](https://core.telegram.org/bots#botfather)
- [Webhook Guide](https://core.telegram.org/bots/webhooks)

---

## Support

For issues or questions:
- Check [GitHub Issues](https://github.com/your-repo/issues)
- Contact: webbografico@codeberg.org
