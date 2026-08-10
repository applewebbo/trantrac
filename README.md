# TranTrac - Family Finance Tracker

A family finance tracking application that automatically syncs transactions to Google Sheets for easy management and reporting.

## Overview

TranTrac helps families track their financial transactions by providing a simple web interface to input expenses and income, with automatic synchronization to Google Sheets. This allows for easy collaboration, reporting, and data analysis using familiar spreadsheet tools.

## Features

- **Transaction Management**: Add, edit, and categorize financial transactions
- **Smart Categorization**: Automatic category suggestions as you type, based on merchant keywords and personal learning
- **PWA Support**: Install as a native app on mobile and desktop (offline-ready)
- **Dark Mode**: Toggle between light and dark theme with persistent preference
- **Keyboard Shortcuts**: `n` for new transaction, `?` for help overlay
- **Telegram Bot**: Quick expense tracking via Telegram with smart category suggestions ([Setup Guide](bot.md))
- **Google Sheets Integration**: Automatic sync of all transactions to Google Sheets
- **CSV Import**: Bulk import transactions from bank CSV exports
- **Category Management**: Organize transactions with categories and subcategories
- **Account Tracking**: Track multiple bank accounts
- **Email Reminders**: Monthly email notifications for transaction review
- **Monthly PDF Reports**: Automatic report generation via management command ([Cron Setup](docs/cron-setup.md))
- **Modern UI**: Built with HTMX and Tailwind CSS for a responsive, app-like experience

## Tech Stack

- **Backend**: Django 6.0+ + Python 3.14+
- **Frontend**: HTMX + Tailwind CSS 4.1.2 + DaisyUI
- **Database**: SQLite with WAL mode
- **Server**: Granian (WSGI) with uvloop
- **Package Management**: uv for Python dependencies
- **Google Sheets API**: Service account integration for data sync
- **Telegram Bot**: python-telegram-bot v22+ with webhook support

## PWA — Install as App

TranTrac is a Progressive Web App. You can install it on any device for a native app experience:

- **Android / Chrome**: tap the browser menu → *Add to Home Screen*
- **iOS / Safari**: tap the Share button → *Add to Home Screen*
- **Desktop / Chrome or Edge**: click the install icon in the address bar

The app works offline for basic navigation and queues actions when connectivity is restored.

## Smart Categorization

When adding a transaction, TranTrac suggests category + subcategory based on the description you type:

1. **Personal learning** — the system learns from your past choices and surfaces your most-used mappings first
2. **Merchant library** — a pre-seeded table of common Italian merchants (Esselunga, Trenitalia, Netflix, etc.)

To seed the merchant library on a fresh install:

```bash
just manage populate_merchant_mappings
```

You can also add or edit merchant mappings in the Django admin under *Mappature merchant*.

## Telegram Bot

TranTrac includes a Telegram bot for quick expense tracking on the go. Features:

- **Simple format**: Send `50/caffè` to record a €50 coffee expense
- **Smart suggestions**: Category suggestions based on your history
- **Instant sync**: Transactions saved directly to Google Sheets
- **Secure auth**: Phone number + email verification

📱 **[Complete Setup Guide](bot.md)** - Learn how to create and configure your bot

## Development

### Prerequisites

- Python 3.14+
- uv (Python package manager)
- bun (for frontend dependencies)

### Setup

```bash
# Clone the repository
git clone https://github.com/applewebbo/trantrac.git
cd trantrac

# Bootstrap the project
just bootstrap

# Run development server
just local
```

### Key commands

| Command | Description |
|---|---|
| `just local` | Dev server with Tailwind watch |
| `just ftest` | Fast parallel tests (100% coverage required) |
| `just lint` | Ruff + pre-commit hooks |
| `just update_all` | Upgrade Python deps + pre-commit hooks + JS libs |
| `just migrate` | Run database migrations |
| `just manage <cmd>` | Run a Django management command |

See `justfile` for the full list.

## Continuous Integration

This project uses Woodpecker CI for automated testing:

- **Test Suite**: Comprehensive pytest test suite with 100% coverage
- **CI Trigger**: Automated tests run on every push to main branch
- **Python Version**: Tests run on Python 3.14
- **Coverage Reports**: Full coverage reporting to ensure code quality

The CI pipeline validates:
- All unit and integration tests pass
- Code maintains 100% test coverage
- Django models, views, and utilities work correctly
- Google Sheets integration functions properly (with mocking)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Enrico Bonardi - [e.bonardi@me.com](https://github.com/applewebbo)
