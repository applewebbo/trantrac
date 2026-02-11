# Cron Setup for Automatic Monthly Reports

TranTrac can automatically generate monthly PDF reports on the 1st of each month
using the `generate_monthly_report` management command.

## Management Command

```bash
python manage.py generate_monthly_report [--year YEAR] [--month MONTH] [--force] [--dry-run]
```

| Option | Description |
|---|---|
| `--year` | Target year (default: auto-detect from current date) |
| `--month` | Target month 1–12 (default: previous month) |
| `--force` | Regenerate even if report already exists |
| `--dry-run` | Show what would be generated without creating files |

**Exit codes:**

| Code | Meaning |
|---|---|
| `0` | Report generated successfully |
| `1` | Error (Google Sheets API failure, PDF generation error, invalid arguments) |
| `2` | Skipped (report already exists or no transactions found) |

## Cron Configuration

Add the following entry to your crontab (`crontab -e`) to run the command at 2 AM
on the 1st of every month:

```cron
0 2 1 * * /path/to/venv/bin/python /path/to/trantrac/manage.py generate_monthly_report >> /var/log/trantrac/reports.log 2>&1
```

With `uv run`:

```cron
0 2 1 * * cd /path/to/trantrac && uv run python manage.py generate_monthly_report >> /var/log/trantrac/reports.log 2>&1
```

Create the log directory first:

```bash
mkdir -p /var/log/trantrac
```

## systemd Timer (alternative to cron)

Create `/etc/systemd/system/trantrac-reports.service`:

```ini
[Unit]
Description=TranTrac monthly report generation
After=network.target

[Service]
Type=oneshot
WorkingDirectory=/path/to/trantrac
ExecStart=uv run python manage.py generate_monthly_report
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/trantrac-reports.timer`:

```ini
[Unit]
Description=Run TranTrac monthly report on the 1st of each month

[Timer]
OnCalendar=*-*-01 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start the timer:

```bash
systemctl enable --now trantrac-reports.timer
systemctl status trantrac-reports.timer
```

## Docker Deployment

When running in Docker, add the cron job to the container's entrypoint or use a
dedicated cron container. Example addition to `entrypoint.sh`:

```bash
# Add to crontab inside container
echo "0 2 1 * * python /app/manage.py generate_monthly_report >> /proc/1/fd/1 2>&1" | crontab -
crond -b
```

## Logging

The command uses Django's logging framework. To persist logs, configure a file
handler in your Django settings:

```python
LOGGING = {
    "version": 1,
    "handlers": {
        "reports_file": {
            "class": "logging.FileHandler",
            "filename": "/var/log/trantrac/reports.log",
        },
    },
    "loggers": {
        "trantrac.management.commands.generate_monthly_report": {
            "handlers": ["reports_file"],
            "level": "INFO",
        },
    },
}
```
