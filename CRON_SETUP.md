# Monthly Reminder Cron Setup (CapRover)

## Overview

Il management command `send_monthly_reminder` invia una mail di reminder agli utenti admin/staff per ricordare di importare le transazioni bancarie mensili.

## Prerequisiti

1. Configurare le variabili d'ambiente in CapRover:
   - `ADMIN_EMAIL`: Email dell'amministratore
   - `MAILGUN_API_KEY`: API key di Mailgun
   - `MAILGUN_API_URL`: URL API di Mailgun
   - `MAILGUN_SENDER_DOMAIN`: Dominio mittente configurato su Mailgun
   - `SITE_URL` (opzionale): URL completo del sito per includere il link diretto al form di upload

2. Assicurarsi che almeno un utente abbia `is_staff=True` o `is_superuser=True`

## Test Manuale

### Trovare il nome del container CapRover

```bash
docker ps | grep trantrac
```

### Eseguire il command

```bash
docker exec srv-captain--trantrac uv run python manage.py send_monthly_reminder
```

**Nota**: Il nome del container di solito è `srv-captain--<app-name>`. Sostituire con il nome effettivo.

## Opzione 1: Cron sul Server CapRover (Consigliato)

Questa è la soluzione più semplice per task mensili.

### 1. Accedere al server CapRover via SSH

```bash
ssh user@your-caprover-server.com
```

### 2. Aprire il crontab

```bash
crontab -e
```

### 3. Aggiungere il cron job

**Ultimo giorno del mese alle 9:00**:
```cron
0 9 28-31 * * [ $(date -d tomorrow +\%d) -eq 1 ] && docker exec srv-captain--trantrac uv run python manage.py send_monthly_reminder >> /var/log/trantrac_cron.log 2>&1
```

**Primo giorno del mese alle 9:00** (alternativa più semplice):
```cron
0 9 1 * * docker exec srv-captain--trantrac uv run python manage.py send_monthly_reminder >> /var/log/trantrac_cron.log 2>&1
```

### 4. Verificare

```bash
crontab -l
```

## Opzione 2: Servizio Web Esterno

Se preferisci non accedere al server, puoi usare un servizio esterno di scheduling.

### 1. Creare un endpoint Django per il cron

Aggiungere in `trantrac/views.py`:

```python
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os

@csrf_exempt
@require_POST
def trigger_monthly_reminder(request):
    # Security: check secret token
    token = request.POST.get('token')
    if token != os.getenv('CRON_SECRET_TOKEN'):
        return HttpResponse('Unauthorized', status=401)

    # Import and execute command
    from django.core.management import call_command
    call_command('send_monthly_reminder')

    return HttpResponse('OK')
```

Aggiungere in `trantrac/urls.py`:
```python
path('cron/monthly-reminder/', views.trigger_monthly_reminder, name='trigger_monthly_reminder'),
```

### 2. Configurare variabile d'ambiente

In CapRover, aggiungere:
- `CRON_SECRET_TOKEN`: Un token segreto casuale

### 3. Configurare servizio esterno

Usare un servizio come:
- **cron-job.org** (gratuito)
- **EasyCron**
- **Zapier** (con schedule trigger)

Configurare una richiesta POST a:
```
https://your-domain.com/cron/monthly-reminder/
```

Con body:
```
token=your-secret-token
```

Schedulare per l'ultimo o primo giorno del mese.

## Log e Monitoraggio

### Visualizzare i log (Opzione 1)

```bash
tail -f /var/log/trantrac_cron.log
```

### Visualizzare i log CapRover (Opzione 2)

Accedere al dashboard CapRover e visualizzare i log dell'applicazione.

## Troubleshooting

1. **Container non trovato**: Verificare il nome con `docker ps | grep trantrac`
2. **Mail non inviate**: Controllare le env vars in CapRover
3. **Permission denied**: L'utente che esegue cron deve avere accesso a Docker
4. **Endpoint non risponde (Opzione 2)**: Verificare che il token sia corretto

## Raccomandazione

Per la massima semplicità, usa **Opzione 1** (cron sul server). È la soluzione più diretta e non richiede modifiche al codice.
