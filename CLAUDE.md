# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Family Finance Tracker that syncs transactions to Google Sheets. Built with Django 5.1, HTMX, Tailwind CSS (via django-tailwind-cli with DaisyUI), and Google Sheets API.

## Tech Stack

- **Backend**: Django 5.1 + Python 3.13+
- **Frontend**: HTMX + Tailwind CSS 4.1.2 + DaisyUI (beta)
- **Database**: SQLite with WAL mode enabled
- **Server**: Granian (WSGI) with uvloop
- **Package Management**: uv for Python
- **Task Runner**: just (see justfile)

## Development Commands

### Setup
```bash
just bootstrap  # Initial setup (requires uv and bun)
just requirements  # Install/sync Python dependencies
```

### Running the App
```bash
just local  # Run dev server with Tailwind watch mode (python manage.py tailwind runserver)
```

### Database
```bash
just migrate  # Run migrations (uses core.settings.development)
python manage.py makemigrations  # Create migrations
```

### Testing
```bash
just test  # Run pytest with coverage (COVERAGE_CORE=sysmon, --reuse-db, -s)
just ftest  # Fast parallel tests (pytest -n 8 --reuse-db)
```

### Code Quality
```bash
just lint  # Run ruff check, ruff format, and pre-commit hooks
```

### Updates
```bash
just update_all  # Upgrade all packages
just update <package>  # Upgrade specific package
```

### Docker
```bash
just docker_up  # Start containers
just docker_build  # Build and start
just docker_down  # Stop and remove volumes
```

## Architecture

### Apps Structure
- **core/**: Project settings, URLs, WSGI/ASGI config
- **trantrac/**: Main app for transaction management, CSV imports, Google Sheets integration
- **users/**: Custom user model with allauth authentication (email-only login)

### Key Components

**Google Sheets Integration** (trantrac/utils.py):
- `get_sheets_service()`: Cached service account credentials connection
- `save_to_sheet(values, sheet_name)`: Append transactions to sheets (ENTRATE/USCITE)
- `import_csv_to_sheet(csv_file, user)`: Parse CSV and sync to Google Sheets, separating positive (ENTRATE) and negative (USCITE) transactions
- `get_sheet_data(sheet_name, range_name)`: Read data from sheets

**Models** (trantrac/models.py):
- `Category` and `Subcategory`: Transaction categories with auto-sync to Google Sheets on save
- `Account`: Bank accounts
- Note: Subcategories use `skip_sheet_save` flag to prevent duplicate saves during bulk operations

**Views** (trantrac/views.py):
- HTMX-powered views with HX-Refresh and HX-Redirect headers
- `index`: Main transaction form
- `upload_csv`: CSV import endpoint
- `load_subcategories`: Dynamic subcategory loading (HTMX)
- `refresh_categories`: Sync categories from Google Sheets to local DB

### Settings Configuration

Uses django-environ for environment variables. Key settings:
- Google Sheets credentials via service account (JSON constructed from env vars)
- Mailgun email backend (django-anymail)
- Custom user model: `users.User` (email-based, no username)
- SQLite with WAL mode and custom PRAGMA settings for performance
- Locale: Italian (it-it, Europe/Rome)

### Frontend

- Templates in `templates/` directory
- HTMX for dynamic interactions
- Tailwind CSS with DaisyUI components
- django-browser-reload for live reloading in development

### Production Deployment

- Dockerfile uses Python 3.13-slim with uv and bun
- Granian WSGI server (2 workers, uvloop, backpressure 16)
- WhiteNoise for static files
- entrypoint.sh: migrate → tailwind build → collectstatic → granian

## Pre-commit Hooks

Configured hooks:
- pyupgrade (--py313-plus)
- django-upgrade (Django 5.1)
- djade (Django template linting)
- ruff (check + format)
- bandit (security)
- rustywind (Tailwind class sorting)
- YAML/TOML formatting

## Testing Strategy

No test files found in the codebase yet. When writing tests:
- Use pytest with `--reuse-db` flag
- Test files should be named `test_*.py`
- Configure conftest.py for fixtures if needed
