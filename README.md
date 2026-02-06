# TranTrac - Family Finance Tracker

A family finance tracking application that automatically syncs transactions to Google Sheets for easy management and reporting.

## Overview

TranTrac helps families track their financial transactions by providing a simple web interface to input expenses and income, with automatic synchronization to Google Sheets. This allows for easy collaboration, reporting, and data analysis using familiar spreadsheet tools.

## Features

- **Transaction Management**: Add, edit, and categorize financial transactions
- **Telegram Bot**: Quick expense tracking via Telegram with smart category suggestions ([Setup Guide](bot.md))
- **Google Sheets Integration**: Automatic sync of all transactions to Google Sheets
- **CSV Import**: Bulk import transactions from bank CSV exports
- **Category Management**: Organize transactions with categories and subcategories
- **Account Tracking**: Track multiple bank accounts
- **Email Reminders**: Monthly email notifications for transaction review
- **Modern UI**: Built with HTMX and Tailwind CSS for a responsive, app-like experience

## Tech Stack

- **Backend**: Django 5.1 + Python 3.13+
- **Frontend**: HTMX + Tailwind CSS 4.1.2 + DaisyUI
- **Database**: SQLite with WAL mode
- **Server**: Granian (WSGI) with uvloop
- **Package Management**: uv for Python dependencies
- **Google Sheets API**: Service account integration for data sync
- **Telegram Bot**: python-telegram-bot v22+ with webhook support

## Telegram Bot

TranTrac includes a Telegram bot for quick expense tracking on the go. Features:

- **Simple format**: Send `50/caffè` to record a €50 coffee expense
- **Smart suggestions**: AI-powered category suggestions based on your history
- **Instant sync**: Transactions saved directly to Google Sheets
- **Secure auth**: Phone number + email verification

📱 **[Complete Setup Guide](bot.md)** - Learn how to create and configure your bot

## Development

### Prerequisites

- Python 3.13+
- uv (Python package manager)
- bun (for frontend dependencies)

### Setup

```bash
# Clone the repository
git clone https://codeberg.org/webbografico/trantrac.git
cd trantrac

# Bootstrap the project
just bootstrap

# Run development server
just local
```

See `justfile` for all available commands.

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

Enrico Bonardi - [webbografico@codeberg.org](https://codeberg.org/webbografico)
