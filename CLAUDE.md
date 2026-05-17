# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Family Finance Tracker that syncs transactions to Google Sheets. Built with Django 5.1, HTMX, Tailwind CSS (via django-tailwind-cli with DaisyUI), and Google Sheets API.

## Tech Stack

- **Backend**: Django 6.0+ + Python 3.14+
- **Frontend**: HTMX + Tailwind CSS 4.1.2 + DaisyUI (beta)
- **Database**: SQLite with WAL mode enabled
- **Server**: Granian (WSGI) with uvloop
- **Package Management**: uv for Python
- **Task Runner**: just (see justfile)
- **Repository**: Codeberg (https://codeberg.org)

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
just test  # Run pytest with coverage
just ftest  # Fast parallel tests (pytest -n 8 --reuse-db, 100% coverage required)
```

### Code Quality
```bash
just lint  # Run ruff check, ruff format, and pre-commit hooks
just lint-stage  # Lint and auto-stage all changes (use before commit)
just secure  # Run uv-secure for security checks
```

### Updates
```bash
just update_all  # Upgrade all packages
just update <package>  # Upgrade specific package
just lock  # Rebuild lock file
```

### Docker
```bash
just docker_up  # Start containers
just docker_build  # Build and start
just docker_down  # Stop and remove volumes
```

### Issue Management (Codeberg)
```bash
just issues [state]  # List issues (state: open|closed|all, default: open)
just issue <number>  # Show issue details
just issue-create <title> [body]  # Create new issue
just issue-comment <number> <text>  # Add comment to issue
just issue-close <number>  # Close issue
just issue-reopen <number>  # Reopen issue
just issue-label <number> <labels>  # Add labels (space-separated)
```

**Note**: The project is hosted on Codeberg. Use the justfile commands above to manage issues instead of GitHub CLI.

## Architecture

### Apps Structure
- **core/**: Project settings, URLs, WSGI/ASGI config
- **trantrac/**: Main app for transaction management, CSV imports, Google Sheets integration
- **users/**: Custom user model with allauth authentication (email-only login)

### Key Components

**Google Sheets Integration** (trantrac/utils.py):
- `get_sheets_service()`: Get Google Sheets API service using credentials from database
- `get_spreadsheet_id()`: Get spreadsheet ID from database settings
- `save_to_sheet(values, sheet_name)`: Append transactions to sheets (ENTRATE/USCITE)
- `import_csv_to_sheet(csv_file, user)`: Parse CSV and sync to Google Sheets, separating positive (ENTRATE) and negative (USCITE) transactions
- `get_sheet_data(sheet_name, range_name)`: Read data from sheets

**Models** (trantrac/models.py):
- `GoogleSheetsSettings`: Singleton model storing Google Sheets API credentials (managed via Django admin)
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
- **Google Sheets**: Configuration managed via Django admin (`GoogleSheetsSettings` model). Initial setup uses env vars, but credentials should be managed through the admin interface after first migration.
- Mailgun email backend (django-anymail)
- Custom user model: `users.User` (email-based, no username)
- SQLite with WAL mode and custom PRAGMA settings for performance
- Locale: Italian (it-it, Europe/Rome)

**Note**: After initial setup, configure Google Sheets credentials in Django admin at `/admin/trantrac/googlesheetssettings/` instead of using environment variables.

### Frontend

- Templates in `templates/` directory
- HTMX for dynamic interactions
- Tailwind CSS with DaisyUI components
- django-browser-reload for live reloading in development

### Production Deployment

- Dockerfile uses Python 3.14-slim with uv and bun
- Granian WSGI server (2 workers, uvloop, backpressure 16)
- WhiteNoise for static files
- entrypoint.sh: migrate → tailwind build → collectstatic → granian

## Pre-commit Hooks

Configured hooks:
- pyupgrade (--py314-plus)
- django-upgrade (Django 6.0)
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
- Coverage must be 100%

## Git Commit Guidelines

- **ALWAYS USE `/commit` SKILL**: Never run `git commit` manually. The skill handles everything:
  - For **full commits** (all changes): Runs `just lint-stage` (lint + auto-stage + pre-commit hooks)
  - For **partial commits** (selected files only): Runs `just lint`, then user manually stages desired files
  - Creates conventional commit with Gitmoji
  - Handles all edge cases (new files, pre-commit fixes, etc.)
- **Partial vs Full Commits**:
  - **Full commit**: All modified files should be included → use `just lint-stage`
  - **Partial commit**: Only specific files should be included → use `just lint`, then `git add <files>` manually
  - ⚠️ **NEVER use `just lint-stage` for partial commits** as it stages ALL files with `git add -A`
- **Conventional Commits**: Format is `<emoji> <type>(<scope>): <description>`
- **Issue References**: Use "for #<number>" in commit message, or "fix #<number>" if closing the issue
- **Language**: Commit messages MUST be in English
- **NO CLAUDE IN COMMITS**: Never cite Claude or AI assistance in commit messages
- **NO AUTO-COMMITS**: Never execute `git commit` autonomously during coding tasks
- **EXCLUSIVE COMMAND**: Only create commits when user explicitly runs `/commit` or asks "please commit"
- **NO PUSH**: Never run `git push` unless explicitly requested

## Claude Code Skills

For detailed skill documentation, workflows, and best practices, read and follow the instructions in `SKILLS.md`.

Available skills: `/commit`, `/makemigrations`, `/check-all`, `/review`, `/release`, `/pre-deploy`, `/db-backup`, `/deps-update`, `/cleanup`

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
