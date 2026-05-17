
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

# Send Telegram reminder (--type monthly|weekly)
[group: 'dev']
remind *args:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run python manage.py send_telegram_reminder {{args}}

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
    fj issue search "" --state {{state}}

# Show issue details
[group: 'codeberg']
issue number:
    fj issue view {{number}}

# Add comment to issue
[group: 'codeberg']
issue-comment number text:
    fj issue comment {{number}} "{{text}}"

# Mark a checkbox step as done in issue body
[group: 'codeberg']
issue-check number step:
    ./bin/codeberg check {{number}} "{{step}}"

# Close issue
[group: 'codeberg']
issue-close number:
    fj issue close {{number}}

# Reopen issue
[group: 'codeberg']
issue-reopen number:
    ./bin/codeberg reopen {{number}}

# Create a label if it doesn't exist (color optional, default blue)
[group: 'codeberg']
label-create name color="#0075ca":
    #!/usr/bin/env bash
    set -euo pipefail
    TOKEN=$(grep "^CODEBERG_API_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    REPO=$(git remote get-url origin | sed 's|.*codeberg.org[:/]\(.*\)\.git|\1|;s|.*codeberg.org[:/]\(.*\)|\1|')
    EXISTING=$(curl -s "https://codeberg.org/api/v1/repos/${REPO}/labels" \
      -H "Authorization: token ${TOKEN}" | jq -r '.[] | select(.name == "{{name}}") | .id')
    if [ -n "$EXISTING" ]; then
        echo "✓ Label '{{name}}' already exists (id: ${EXISTING})"
    else
        curl -s -X POST "https://codeberg.org/api/v1/repos/${REPO}/labels" \
          -H "Authorization: token ${TOKEN}" \
          -H "Content-Type: application/json" \
          -d '{"name":"{{name}}","color":"{{color}}"}' | jq -r '"✓ Label \(.name) created (id: \(.id))"'
    fi

# Add labels to issue (space-separated label names)
[group: 'codeberg']
issue-label number *labels:
    #!/usr/bin/env bash
    set -euo pipefail
    for label in {{labels}}; do
        fj issue edit {{number}} labels -a "$label"
        echo "✓ Label '$label' added to issue #{{number}}"
    done

# Create a label (if missing, with random color) and assign it to an issue
[group: 'codeberg']
issue-label-create number name:
    #!/usr/bin/env bash
    set -euo pipefail
    COLORS=("#e11d48" "#ea580c" "#d97706" "#65a30d" "#16a34a" "#059669" "#0891b2" "#2563eb" "#7c3aed" "#c026d3" \
            "#be185d" "#b45309" "#4d7c0f" "#0e7490" "#1d4ed8" "#6d28d9" "#a21caf" "#be123c" "#15803d" "#0369a1")
    RANDOM_COLOR=${COLORS[$((RANDOM % ${#COLORS[@]}))]}
    TOKEN=$(grep "^CODEBERG_API_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    REPO=$(git remote get-url origin | sed 's|.*codeberg.org[:/]\(.*\)\.git|\1|;s|.*codeberg.org[:/]\(.*\)|\1|')
    LABEL_ID=$(curl -s "https://codeberg.org/api/v1/repos/${REPO}/labels" \
      -H "Authorization: token ${TOKEN}" | jq -r '.[] | select(.name == "{{name}}") | .id')
    if [ -z "$LABEL_ID" ]; then
        echo "Creating label '{{name}}' with color ${RANDOM_COLOR}..."
        LABEL_ID=$(curl -s -X POST "https://codeberg.org/api/v1/repos/${REPO}/labels" \
          -H "Authorization: token ${TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{\"name\":\"{{name}}\",\"color\":\"${RANDOM_COLOR}\"}" | jq -r '.id')
        echo "✓ Label '{{name}}' created (id: ${LABEL_ID})"
    else
        echo "✓ Label '{{name}}' already exists (id: ${LABEL_ID})"
    fi
    fj issue edit {{number}} labels -a "{{name}}"
    echo "✓ Label assigned to issue #{{number}}"

# Create new issue (body optional)
[group: 'codeberg']
issue-create title body="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{body}}" ]; then
        EDITOR=true fj issue create "{{title}}" --no-template
    else
        TMPFILE=$(mktemp /tmp/issue-body-XXXXXX.md)
        echo "{{body}}" > "$TMPFILE"
        EDITOR=true fj issue create "{{title}}" --body-file "$TMPFILE" --no-template
        rm "$TMPFILE"
    fi

# Edit issue body from file (usage: just issue-edit-body 42 /path/to/body.md)
[group: 'codeberg']
issue-edit-body number file:
    fj issue edit {{number}} body "$(cat {{file}})"

# Create a pull request from current branch to main
[group: 'codeberg']
pr-create title body="" base="main":
    fj pr create -t "{{title}}" -b "{{body}}" -B "{{base}}" -H "$(git branch --show-current)"

# ============================================================================
# Codeberg Releases
# ============================================================================

# List all releases
[group: 'codeberg']
release-list:
    fj release list --include-draft --include-prerelease

# Show release details
[group: 'codeberg']
release-show tag:
    fj release view "{{tag}}" --by-tag

# Create a new release (creates tag, pushes main+tag, creates Codeberg release via fj)
# Pass notes_file to use custom rich notes; omit for auto-generated notes from commits
[group: 'codeberg']
release-create tag previous_tag="" notes_file="" draft="false" prerelease="false":
    #!/usr/bin/env bash
    set -euo pipefail

    REPO=$(git remote get-url origin | sed 's|.*codeberg.org[:/]\(.*\)\.git|\1|;s|.*codeberg.org[:/]\(.*\)|\1|')

    # Push main to origin
    echo "📤 Pushing main to origin..."
    git push origin main
    echo "✓ main pushed to origin"

    # Check if tag already exists locally
    if git rev-parse "{{tag}}" >/dev/null 2>&1; then
        echo "✓ Tag {{tag}} already exists locally"
    else
        echo "📝 Creating tag {{tag}} on current commit..."
        git tag "{{tag}}"
        echo "✓ Tag {{tag}} created"
    fi

    # Push tag to origin (use refs/tags/ to avoid branch/tag ambiguity)
    echo "📤 Pushing tag {{tag}} to origin..."
    git push origin "refs/tags/{{tag}}"
    echo "✓ Tag {{tag}} pushed to origin"

    # Determine notes file
    if [ "{{notes_file}}" != "" ]; then
        NOTES_FILE="{{notes_file}}"
        echo "📄 Using provided notes file: ${NOTES_FILE}"
    else
        NOTES_FILE=$(mktemp /tmp/release-notes-XXXXXX.md)

        if [ "{{previous_tag}}" = "" ]; then
            PREV_TAG=$(git tag --sort=-version:refname | grep -v "{{tag}}" | head -1)
        else
            PREV_TAG="{{previous_tag}}"
        fi

        echo "🔍 Generating release notes (comparing with ${PREV_TAG})..."
        COMMITS=$(git log ${PREV_TAG}..{{tag}} --pretty=format:"- %s" --reverse 2>/dev/null || echo "- Initial release")

        FEATURES=$(echo "$COMMITS" | grep -E "^- (✨|feat)" || true)
        FIXES=$(echo "$COMMITS" | grep -E "^- (🐛|fix)" || true)
        CHORES=$(echo "$COMMITS" | grep -E "^- (🔧|chore|📦|build|🎨)" || true)
        TESTS=$(echo "$COMMITS" | grep -E "^- (🧪|test|✅)" || true)
        DOCS=$(echo "$COMMITS" | grep -E "^- (📚|docs)" || true)

        {
            echo "## What's New in {{tag}}"
            echo ""
            if [ -n "$FEATURES" ]; then
                echo "### 🚀 Features"
                echo "$FEATURES"
                echo ""
            fi
            if [ -n "$FIXES" ]; then
                echo "### 🐛 Bug Fixes"
                echo "$FIXES"
                echo ""
            fi
            if [ -n "$CHORES" ]; then
                echo "### 🛠️ Maintenance"
                echo "$CHORES"
                echo ""
            fi
            if [ -n "$TESTS" ]; then
                echo "### 🧪 Testing"
                echo "$TESTS"
                echo ""
            fi
            if [ -n "$DOCS" ]; then
                echo "### 📖 Documentation"
                echo "$DOCS"
                echo ""
            fi
            echo "### 📖 Full Changelog"
            echo "https://codeberg.org/${REPO}/compare/${PREV_TAG}...{{tag}}"
        } > "$NOTES_FILE"
    fi

    # Create release via fj
    echo "🚀 Creating release on Codeberg..."
    fj release create "{{tag}}" -r "$REPO" --tag "{{tag}}" --body "$(cat "$NOTES_FILE")"
    echo ""
    echo "✓ Release {{tag}} created!"

# Delete a release (use with caution!)
[group: 'codeberg']
release-delete tag:
    fj release delete {{tag}}

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
