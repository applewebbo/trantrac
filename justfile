
# Define the default recipe
default:
    @just --list

# ============================================================================
# Setup
# ============================================================================

# Bootstrap the project (UV and BUN needed)
[group: 'setup']
bootstrap:
    uv venv
    source .venv/bin/activate
    uv sync
    bun add -D daisyui@beta

# Install requirements
[group: 'setup']
requirements:
    uv sync

# ============================================================================
# Development
# ============================================================================

# Run the local development server
[group: 'dev']
local:
    uv run python manage.py tailwind runserver --force-default-runserver

# Run the Telegram bot (polling mode)
[group: 'dev']
runbot:
    uv run python manage.py runbot

# ============================================================================
# Database
# ============================================================================

# Run database migrations
[group: 'database']
migrate:
    uv run python manage.py migrate

# ============================================================================
# Testing
# ============================================================================

# Run tests with coverage
[group: 'test']
test:
    uv run pytest tests/

# Run fast parallel tests with coverage
[group: 'test']
ftest:
    uv run pytest tests/ -n 8 --reuse-db --cov --cov-report=term-missing --cov-fail-under=100

# Run tests with coverage report
[group: 'test']
test-cov:
    uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing

# ============================================================================
# Code Quality
# ============================================================================

[group: 'quality']
lint:
    uv run ruff check --fix --unsafe-fixes .
    uv run ruff format .
    just _pre-commit run --all-files
    @echo "\n✓ Lint completato"
    @echo "⚠️  Se ci sono file modificati, devono essere ri-staged:"
    @git status --short 2>/dev/null | head -10 || true

# Lint and auto-stage all changes (use before commit)
[group: 'quality']
lint-stage:
    just lint
    @echo "\n📦 Auto-staging delle modifiche..."
    git add -A
    @echo "\n🔍 Eseguo pre-commit sui file staged..."
    just _pre-commit run || true
    @echo "\n📦 Re-staging dopo pre-commit fixes..."
    git add -A
    @echo "✓ File staged. Pronto per il commit"
    @git status --short

[group: 'quality']
secure:
    uv-secure

_pre-commit *args:
    uvx prek {{ args }}

# ============================================================================
# Dependencies
# ============================================================================

# Update all packages
[group: 'dependencies']
@update_all: lock
    uv sync --all-extras --upgrade
    uvx --with pre-commit-uv prek auto-update

[group: 'dependencies']
@lock:
    echo "Rebuilding lock file..."
    uv lock --upgrade
    echo "Done!"

# Update a specific package
[group: 'dependencies']
update package:
    uv sync --upgrade-package {{package}}

# ============================================================================
# Docker
# ============================================================================

[group: 'docker']
docker_up:
    docker compose up -d

[group: 'docker']
docker_build:
    docker compose up -d --build

[group: 'docker']
docker_down:
    docker compose down -v

# ============================================================================
# Codeberg Issues
# ============================================================================

# List issues (state: open|closed|all)
[group: 'codeberg']
issues state="open":
    ./bin/codeberg list {{state}}

# Show issue details
[group: 'codeberg']
issue number:
    ./bin/codeberg show {{number}}

# Add comment to issue
[group: 'codeberg']
issue-comment number text:
    ./bin/codeberg comment {{number}} "{{text}}"

# Close issue
[group: 'codeberg']
issue-close number:
    ./bin/codeberg close {{number}}

# Reopen issue
[group: 'codeberg']
issue-reopen number:
    ./bin/codeberg reopen {{number}}

# Add labels to issue (space-separated)
[group: 'codeberg']
issue-label number *labels:
    ./bin/codeberg label {{number}} {{labels}}

# Create new issue
[group: 'codeberg']
issue-create title body="":
    ./bin/codeberg create "{{title}}" "{{body}}"
