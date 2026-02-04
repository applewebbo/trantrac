# Deployment

## Setup BotFather

### 1. Crea Bot

```
1. Apri @BotFather su Telegram
2. Invia: /newbot
3. Nome: TranTrac Bot
4. Username: trantrac_bot (o altro disponibile)
5. Copia TELEGRAM_BOT_TOKEN
```

### 2. Configura Comandi

```
/setcommands

start - Collega il tuo account e inizia
help - Mostra aiuto

/setdescription

Bot per inserire spese su TranTrac. Invia le tue transazioni direttamente da Telegram!

/setabouttext

TranTrac Bot - Gestione spese familiari
```

## Environment Variables

### `.env` Development (Polling Mode)

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_URL=
TELEGRAM_WEBHOOK_SECRET=
SITE_URL=http://localhost:8000
```

### `.env` Production (Webhook Mode)

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_WEBHOOK_URL=https://trantrac.com/telegram/webhook/
TELEGRAM_WEBHOOK_SECRET=your-random-secret-here-use-openssl-rand
SITE_URL=https://trantrac.com
```

**Genera secret**:
```bash
openssl rand -hex 32
```

### `.env.example`

```bash
# ... existing vars ...

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/telegram/webhook/
TELEGRAM_WEBHOOK_SECRET=random_secret_for_validation
SITE_URL=https://yourdomain.com
```

## Dependencies

```bash
uv add python-telegram-bot[webhook]
```

## Development: Polling Mode

### 1. Setup

```bash
# .env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_URL=  # lascia vuoto
```

### 2. Run

```bash
python manage.py runbot
```

**Output**:
```
Bot started in polling mode
```

### 3. Test

Invia `/start` al bot su Telegram → dovrebbe rispondere

## Production: Webhook Mode

### 1. Setup

```bash
# .env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_URL=https://trantrac.com/telegram/webhook/
TELEGRAM_WEBHOOK_SECRET=$(openssl rand -hex 32)
```

### 2. Deploy

```bash
# Migrations
python manage.py makemigrations users
python manage.py makemigrations telegram_bot
python manage.py migrate

# Collectstatic (se necessario)
python manage.py collectstatic --noinput
```

### 3. Set Webhook

```bash
python manage.py setwebhook
```

**Output**:
```
Webhook set successfully
URL: https://trantrac.com/telegram/webhook/
```

### 4. Verify

```bash
curl "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getWebhookInfo"
```

**Response**:
```json
{
  "ok": true,
  "result": {
    "url": "https://trantrac.com/telegram/webhook/",
    "has_custom_certificate": false,
    "pending_update_count": 0,
    "max_connections": 40
  }
}
```

## Management Command: setwebhook

**File**: `management/commands/setwebhook.py`

```python
from django.core.management.base import BaseCommand
from django.conf import settings
import requests

class Command(BaseCommand):
    help = 'Set Telegram webhook'

    def handle(self, *args, **options):
        if not settings.TELEGRAM_WEBHOOK_URL:
            self.stdout.write(self.style.ERROR('TELEGRAM_WEBHOOK_URL not set'))
            return

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook"

        data = {
            'url': settings.TELEGRAM_WEBHOOK_URL,
            'secret_token': settings.TELEGRAM_WEBHOOK_SECRET,
        }

        response = requests.post(url, json=data)
        result = response.json()

        if result.get('ok'):
            self.stdout.write(self.style.SUCCESS('Webhook set successfully'))
            self.stdout.write(f"URL: {settings.TELEGRAM_WEBHOOK_URL}")
        else:
            self.stdout.write(self.style.ERROR(f"Failed: {result}"))
```

## Cronjobs

### retry_pending_transactions

```bash
# crontab -e
*/15 * * * * cd /path/to/trantrac && /path/to/venv/bin/python manage.py retry_pending_transactions >> /var/log/telegram_retry.log 2>&1
```

### cleanup_auth_sessions

```bash
# crontab -e
0 * * * * cd /path/to/trantrac && /path/to/venv/bin/python manage.py cleanup_auth_sessions >> /var/log/telegram_cleanup.log 2>&1
```

## NGINX Configuration

```nginx
# telegram webhook endpoint
location /telegram/webhook/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Security
    client_max_body_size 1M;
    proxy_read_timeout 30s;
}
```

## Systemd Service (Optional)

Se vuoi usare polling mode in produzione:

```ini
# /etc/systemd/system/trantrac-bot.service
[Unit]
Description=TranTrac Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/trantrac
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py runbot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable trantrac-bot
sudo systemctl start trantrac-bot
sudo systemctl status trantrac-bot
```

## Health Check

### Webhook Endpoint

```python
# telegram_bot/views.py
from django.http import JsonResponse

def health_check(request):
    """Health check for monitoring"""
    from telegram_bot.models import PendingTransaction

    pending_count = PendingTransaction.objects.filter(status='pending').count()
    failed_count = PendingTransaction.objects.filter(status='failed').count()

    return JsonResponse({
        'status': 'ok',
        'pending_transactions': pending_count,
        'failed_transactions': failed_count,
    })
```

```python
# telegram_bot/urls.py
urlpatterns = [
    path('webhook/', telegram_webhook, name='telegram_webhook'),
    path('health/', health_check, name='health_check'),
]
```

**Test**:
```bash
curl https://trantrac.com/telegram/health/
```

## Monitoring

### Logs

```bash
# Webhook logs
tail -f /var/log/nginx/access.log | grep telegram

# Retry logs
tail -f /var/log/telegram_retry.log

# Django logs
tail -f /path/to/logs/django.log
```

### Metrics to Track

1. **Success Rate**: `save_to_sheet()` success vs failures
2. **Pending Transactions**: count and age
3. **Response Time**: webhook response < 2s
4. **Retry Performance**: pending → completed time

### Simple Dashboard

```python
# admin dashboard
from django.db.models import Count, Q
from telegram_bot.models import PendingTransaction

stats = {
    'pending': PendingTransaction.objects.filter(status='pending').count(),
    'processing': PendingTransaction.objects.filter(status='processing').count(),
    'completed_today': PendingTransaction.objects.filter(
        status='completed',
        created_at__date=timezone.now().date()
    ).count(),
    'failed': PendingTransaction.objects.filter(status='failed').count(),
}
```

## Troubleshooting

### Webhook not receiving updates

```bash
# 1. Check webhook info
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"

# 2. Delete webhook (reset)
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# 3. Set again
python manage.py setwebhook
```

### Bot not responding

```bash
# 1. Check logs
tail -f /var/log/telegram_retry.log

# 2. Test webhook manually
curl -X POST https://trantrac.com/telegram/webhook/ \
  -H "Content-Type: application/json" \
  -H "X-Telegram-Bot-Api-Secret-Token: YOUR_SECRET" \
  -d '{"update_id": 1, "message": {"text": "/start"}}'

# 3. Check Django logs for errors
```

### Rate limiting issues

```bash
# Check if hitting Telegram rate limits
# Telegram allows 30 messages/second

# Check Google Sheets quota
# Monitor PendingTransaction count
```

## Rollback Plan

Se qualcosa va storto:

```bash
# 1. Delete webhook (fall back to web only)
curl "https://api.telegram.org/bot<TOKEN>/deleteWebhook"

# 2. Rollback migrations (if needed)
python manage.py migrate telegram_bot zero
python manage.py migrate users <previous_migration>

# 3. Remove from INSTALLED_APPS
# Edit settings.py

# 4. Restart Django
sudo systemctl restart gunicorn
```
