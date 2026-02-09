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

Custom skills available for common Django workflows. Use these for automated quality checks and safe operations.

### Available Skills

#### `/makemigrations` - Safe Migration Creation
**Use when:** Modifying Django models

**What it does:**
1. Runs `just ftest` to ensure tests pass before creating migrations
2. Shows preview with `--dry-run` to review changes
3. Detects dangerous operations (RenameField, RemoveField, AddField without default)
4. Asks for confirmation before creating
5. Creates migrations and re-runs tests to verify
6. Reminds to commit migrations and update related beans

**Example workflow:**
```bash
# After modifying models.py
/makemigrations
# Review preview, confirm
# Migrations created and tested
# Then: /commit to commit migrations
```

#### `/check-all` - Comprehensive Health Check
**Use when:** Before commits, before deployments, during code reviews

**What it does:**
1. Django system checks (dev + deploy mode)
2. Migration status verification
3. Code quality check (`just lint`)
4. Security audit (`just secure`)
5. Full test suite with 100% coverage (`just ftest`)
6. Counts TODO/FIXME comments
7. Lists open beans

**Output:** Health report with overall status (HEALTHY ✅ / NEEDS ATTENTION ⚠️ / FAILING ❌)

**Recommended:** Run before every important commit or merge

#### `/pre-deploy` - Pre-Deployment Checklist
**Use when:** Before production deployments

**What it does:**
1. Runs full `/check-all` health check
2. Verifies production settings:
   - `DEBUG = False`
   - `SECRET_KEY` from environment
   - `ALLOWED_HOSTS` configured
   - CSRF/Session cookie security enabled
3. Tests static files collection (`collectstatic --dry-run`)
4. Builds and tests Docker image (`just docker_build`)
5. Verifies git status (clean, correct branch, synced with remote)
6. Presents interactive deployment checklist
7. Provides deployment commands and recommendations

**Critical:** MUST be run before every production deployment

#### `/db-backup` - Database Backup
**Use when:** Before risky operations, before deployments, periodic backups

**What it does:**
1. Checks disk space and database status
2. Creates timestamped JSON backup with `dumpdata` (portable format)
3. Creates timestamped SQLite backup (fast restore)
4. Verifies backup integrity
5. Compresses backups with gzip
6. Shows restore commands
7. Suggests backup rotation policy

**Output:** Two backup files:
- `backups/db_backup_YYYYMMDD_HHMMSS.json.gz` (portable, for migration)
- `backups/db_sqlite3_YYYYMMDD_HHMMSS.db.gz` (fast restore)

**Backup before:**
- Migrations with potential data loss
- Database schema changes
- Production deployments
- Database reset operations

### Recommended Workflows

#### Normal Development
```bash
# 1. Make code changes
# 2. Verify everything is OK
/check-all

# 3. If all checks pass, commit
/commit
```

#### Model Changes
```bash
# 1. Modify models.py
# 2. Create migrations safely
/makemigrations

# 3. Review and commit migrations
/commit
```

#### Pre-Deployment
```bash
# 1. Backup database first
/db-backup

# 2. Run comprehensive pre-deployment checks
/pre-deploy

# 3. If all checks ✅, proceed with deployment
# Follow deployment commands provided by skill
```

#### Before Risky Operations
```bash
# Always backup first
/db-backup

# Then proceed with risky operation
# (migrations, schema changes, bulk updates, etc.)
```

### Skill Integration with Beans

- **`/makemigrations`**: Reminds to update related beans after creating migrations
- **`/check-all`**: Shows count of open beans ready to work on
- **`/pre-deploy`**: Suggests marking completed beans as done before release
- **`/commit`**: Include bean file changes in commits when using beans for task tracking

### Best Practices

1. **Use `/check-all` liberally**: Run before every significant commit
2. **Never skip `/pre-deploy`**: Critical for production safety
3. **Backup before risk**: Use `/db-backup` before any potentially destructive operation
4. **Trust the automation**: Skills handle edge cases and provide comprehensive checks
5. **Follow the prompts**: Skills ask for confirmation when needed - review carefully
