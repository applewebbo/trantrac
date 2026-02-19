
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
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run pytest tests/ -n 8 --reuse-db --cov --cov-report=term-missing --cov-fail-under=100

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

# Mark a checkbox step as done in issue body
[group: 'codeberg']
issue-check number step:
    ./bin/codeberg check {{number}} "{{step}}"

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

# ============================================================================
# Codeberg Releases
# ============================================================================

# List all releases
[group: 'codeberg']
release-list:
    #!/usr/bin/env bash
    set -euo pipefail
    TOKEN=$(grep "^CODEBERG_API_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    echo -e "TAG\tNAME\tPUBLISHED\tDRAFT"
    curl -s "https://codeberg.org/api/v1/repos/webbografico/trantrac/releases" \
      -H "Authorization: token ${TOKEN}" | \
      jq -r '.[] | "\(.tag_name)\t\(.name)\t\(.published_at)\t\(.draft)"' | \
      column -t -s $'\t'

# Show release details
[group: 'codeberg']
release-show tag:
    #!/usr/bin/env bash
    set -euo pipefail
    TOKEN=$(grep "^CODEBERG_API_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    curl -s "https://codeberg.org/api/v1/repos/webbografico/trantrac/releases/tags/{{tag}}" \
      -H "Authorization: token ${TOKEN}" | \
      jq -r '"\nTag: \(.tag_name)\nName: \(.name)\nPublished: \(.published_at)\nDraft: \(.draft)\nPrerelease: \(.prerelease)\n\nURL: \(.html_url)\n\nBody:\n\(.body)\n"'

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

    # Get token
    TOKEN=$(grep "^CODEBERG_API_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")

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
    BODY="## What's New in {{tag}}\n\n"

    if [ -n "$FEATURES" ]; then
        BODY+="### 🚀 Features\n$FEATURES\n\n"
    fi

    if [ -n "$FIXES" ]; then
        BODY+="### 🐛 Bug Fixes\n$FIXES\n\n"
    fi

    if [ -n "$CHORES" ]; then
        BODY+="### 🛠️ Maintenance\n$CHORES\n\n"
    fi

    if [ -n "$TESTS" ]; then
        BODY+="### 🧪 Testing\n$TESTS\n\n"
    fi

    if [ -n "$DOCS" ]; then
        BODY+="### 📖 Documentation\n$DOCS\n\n"
    fi

    BODY+="### 📖 Full Changelog\nhttps://codeberg.org/webbografico/trantrac/compare/${PREV_TAG}...{{tag}}"

    # Create release via API
    echo "🚀 Creating release on Codeberg..."
    curl -X POST "https://codeberg.org/api/v1/repos/webbografico/trantrac/releases" \
      -H "Authorization: token ${TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"tag_name\": \"{{tag}}\",
        \"name\": \"Release {{tag}}\",
        \"body\": \"${BODY}\",
        \"draft\": {{draft}},
        \"prerelease\": {{prerelease}}
      }" | jq -r '"\n✓ Release created successfully!\nURL: \(.html_url)\n"'

# Delete a release (use with caution!)
[group: 'codeberg']
release-delete tag:
    #!/usr/bin/env bash
    set -euo pipefail
    TOKEN=$(grep "^CODEBERG_API_TOKEN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    echo "⚠️  Deleting release {{tag}}..."
    curl -X DELETE "https://codeberg.org/api/v1/repos/webbografico/trantrac/releases/tags/{{tag}}" \
      -H "Authorization: token ${TOKEN}"
    echo "✓ Release {{tag}} deleted"

# ============================================================================
# Beans
# ============================================================================

# List active beans (excludes completed and scrapped)
[group: 'beans']
beans:
    beans list --no-status completed --no-status scrapped
