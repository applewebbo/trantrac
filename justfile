
# Define the default recipe
default:
    @just --list

##########################################################################
# Setup
##########################################################################

# Ensure project virtualenv is up to date
[group('setup')]
@install:
    uv sync

# Remove temporary files
[group('setup')]
clean:
    rm -rf .venv .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov .django_tailwind_cli
    find . -type d -name "__pycache__" -exec rm -r {} +

# Recreate project virtualenv from nothing
[group('setup')]
fresh: clean install

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

# Generate monthly PDF  (defaults to previous month)
[group: 'dev']
report *args:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run python manage.py generate_monthly_report {{args}}

# ============================================================================
# Database
# ============================================================================

# Run database migrations
[group: 'database']
migrate:
    uv run python manage.py migrate

# Run any Django management command
[group: 'database']
manage *args:
    uv run python manage.py {{args}}

# ============================================================================
# Testing
# ============================================================================

# Run tests with coverage
[group: 'test']
test:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run pytest tests/

# Run fast parallel tests with coverage
[group: 'test']
ftest:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib PYTHONWARNINGS="ignore::DeprecationWarning:pytest_asyncio.plugin" uv run pytest tests/ -n 8 --reuse-db --cov --cov-report=term-missing --cov-fail-under=100

# Run tests with coverage report
[group: 'test']
test-cov:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing

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

# Update all packages (Python deps + pre-commit hooks + JS libs)
[group: 'dependencies']
@update_all: lock update_js
    uv sync --all-extras --upgrade
    uvx --with pre-commit-uv prek auto-update

# Update vendored JS libraries in static/js/ to their latest versions
[group: 'dependencies']
update_js:
    #!/usr/bin/env bash
    set -euo pipefail
    JS_DIR="static/js"
    echo "Updating JS libraries..."
    curl -fsSL "https://unpkg.com/htmx.org@latest/dist/htmx.min.js" -o "$JS_DIR/htmx.min.js"
    echo "  ✓ htmx.min.js"
    curl -fsSL "https://unpkg.com/alpinejs@latest/dist/cdn.min.js" -o "$JS_DIR/alpine.min.js"
    echo "  ✓ alpine.min.js"
    curl -fsSL "https://unpkg.com/@alpinejs/collapse@latest/dist/cdn.min.js" -o "$JS_DIR/alpine-collapse.min.js"
    echo "  ✓ alpine-collapse.min.js"
    echo "Done!"

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
    fgj issue list -s {{state}}

# Show issue details
[group: 'codeberg']
issue number:
    fgj issue view {{number}}

# Add comment to issue
[group: 'codeberg']
issue-comment number text:
    fgj issue comment {{number}} -b "{{text}}"

# Close issue
[group: 'codeberg']
issue-close number:
    fgj issue close {{number}}

# Reopen issue
[group: 'codeberg']
issue-reopen number:
    fgj issue edit {{number}} -s open

# Add labels to issue (space-separated)
[group: 'codeberg']
issue-label number *labels:
    #!/usr/bin/env bash
    set -euo pipefail
    for label in {{labels}}; do
        fgj issue edit {{number}} --add-label "$label"
    done

# Create new issue
[group: 'codeberg']
issue-create title body="":
    fgj issue create -t "{{title}}" -b "{{body}}"

# Edit issue title and/or body
[group: 'codeberg']
issue-edit number title="" body="":
    #!/usr/bin/env bash
    set -euo pipefail
    ARGS=""
    [ -n "{{title}}" ] && ARGS="$ARGS -t '{{title}}'"
    [ -n "{{body}}" ] && ARGS="$ARGS -b '{{body}}'"
    eval fgj issue edit {{number}} $ARGS

# Create a pull request from current branch to main
[group: 'codeberg']
pr-create title body="" base="main":
    fgj pr create -t "{{title}}" -b "{{body}}" -B "{{base}}" -H "$(git branch --show-current)"

# ============================================================================
# Codeberg Releases
# ============================================================================

# List all releases
[group: 'codeberg']
release-list:
    fgj release list

# Show release details
[group: 'codeberg']
release-show tag:
    fgj release view {{tag}}

# Create a new release (auto-creates tag, pushes it, and generates notes from commits)
[group: 'codeberg']
release-create tag previous_tag="" draft="false" prerelease="false":
    #!/usr/bin/env bash
    set -euo pipefail

    # Check if tag already exists locally
    if git rev-parse "{{tag}}" >/dev/null 2>&1; then
        echo "✓ Tag {{tag}} already exists locally"
    else
        echo "📝 Creating tag {{tag}} on current commit..."
        git tag "{{tag}}"
        echo "✓ Tag {{tag}} created"
    fi

    # Push tag to origin
    echo "📤 Pushing tag {{tag}} to origin..."
    if git push origin "{{tag}}" 2>&1 | grep -q "already exists"; then
        echo "✓ Tag {{tag}} already exists on remote"
    else
        echo "✓ Tag {{tag}} pushed to origin"
    fi

    # Determine previous tag if not provided
    if [ "{{previous_tag}}" = "" ]; then
        PREV_TAG=$(git tag --sort=-version:refname | grep -v "{{tag}}" | head -1)
    else
        PREV_TAG="{{previous_tag}}"
    fi

    echo "🔍 Generating release notes (comparing with ${PREV_TAG})..."

    # Generate release notes from commits
    COMMITS=$(git log ${PREV_TAG}..{{tag}} --pretty=format:"- %s" --reverse 2>/dev/null || echo "- Initial release")

    # Parse commits into categories
    FEATURES=$(echo "$COMMITS" | grep -E "^- (✨|feat)" || true)
    FIXES=$(echo "$COMMITS" | grep -E "^- (🐛|fix)" || true)
    CHORES=$(echo "$COMMITS" | grep -E "^- (🔧|chore|📦|build|🎨)" || true)
    TESTS=$(echo "$COMMITS" | grep -E "^- (🧪|test|✅)" || true)
    DOCS=$(echo "$COMMITS" | grep -E "^- (📚|docs)" || true)

    # Build release body
    NL=$'\n'
    BODY="## What's New in {{tag}}${NL}${NL}"

    if [ -n "$FEATURES" ]; then
        BODY+="### 🚀 Features${NL}$FEATURES${NL}${NL}"
    fi

    if [ -n "$FIXES" ]; then
        BODY+="### 🐛 Bug Fixes${NL}$FIXES${NL}${NL}"
    fi

    if [ -n "$CHORES" ]; then
        BODY+="### 🛠️ Maintenance${NL}$CHORES${NL}${NL}"
    fi

    if [ -n "$TESTS" ]; then
        BODY+="### 🧪 Testing${NL}$TESTS${NL}${NL}"
    fi

    if [ -n "$DOCS" ]; then
        BODY+="### 📖 Documentation${NL}$DOCS${NL}${NL}"
    fi

    BODY+="### 📖 Full Changelog${NL}https://codeberg.org/webbografico/trantrac/compare/${PREV_TAG}...{{tag}}"

    # Write notes to temp file to avoid shell escaping issues
    NOTES_FILE=$(mktemp)
    echo "$BODY" > "$NOTES_FILE"

    # Create release via fgj
    echo "🚀 Creating release on Codeberg..."
    DRAFT_FLAG=""
    PRERELEASE_FLAG=""
    [ "{{draft}}" = "true" ] && DRAFT_FLAG="--draft"
    [ "{{prerelease}}" = "true" ] && PRERELEASE_FLAG="--prerelease"

    fgj release create "{{tag}}" \
        --title "{{tag}}" \
        --notes-file "$NOTES_FILE" \
        $DRAFT_FLAG $PRERELEASE_FLAG

    rm -f "$NOTES_FILE"
    echo "✓ Release {{tag}} created successfully!"

# Delete a release (use with caution!)
[group: 'codeberg']
release-delete tag:
    fgj release delete {{tag}}

# ============================================================================
# Beans
# ============================================================================

# List active beans (excludes completed and scrapped)
[group: 'beans']
beans:
    beans list --ready

# List completed beans
[group: 'beans']
beans_completed:
    beans list -s completed
