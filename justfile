
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

# Run tests with coverage (extra pytest args are forwarded)
[group: 'test']
test *args:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run pytest tests/ {{args}}

# Run fast parallel tests with coverage (extra pytest args are forwarded, e.g. just ftest --last-failed)
[group: 'test']
ftest *args:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib PYTHONWARNINGS="ignore::DeprecationWarning:pytest_asyncio.plugin" uv run pytest tests/ -n 8 --reuse-db --cov --cov-report=term-missing --cov-fail-under=100 {{args}}

# Run tests with coverage report (extra pytest args are forwarded)
[group: 'test']
test-cov *args:
    DYLD_LIBRARY_PATH=/opt/homebrew/lib uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing {{args}}

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
# GitHub Issues
# ============================================================================

github_repo := "applewebbo/trantrac"

# List issues (state: open|closed|all)
[group: 'github']
issues state="open":
    gh issue list -R {{github_repo}} --state {{state}} --limit 100

# Show issue details
[group: 'github']
issue number:
    gh issue view {{number}} -R {{github_repo}} --comments

# Add comment to issue
[group: 'github']
issue-comment number text:
    gh issue comment {{number}} -R {{github_repo}} --body {{quote(text)}}

# Mark a checkbox step as done in issue body
[group: 'github']
issue-check number step:
    #!/usr/bin/env bash
    set -euo pipefail
    BODY=$(gh issue view {{number}} -R {{github_repo}} --json body --jq .body)
    NEW_BODY=$(STEP={{quote(step)}} python3 -c 'import os, re, sys; step = os.environ["STEP"]; new, n = re.subn(r"^(\s*[-*] )\[ \](\s*.*" + re.escape(step) + r".*)$", r"\1[x]\2", sys.stdin.read(), count=1, flags=re.MULTILINE); sys.stdout.write(new) if n else sys.exit("Step not found: " + step)' <<< "$BODY")
    gh issue edit {{number}} -R {{github_repo}} --body "$NEW_BODY"
    echo "✓ Step checked on issue #{{number}}"

# Close issue
[group: 'github']
issue-close number:
    gh issue close {{number}} -R {{github_repo}}

# Reopen issue
[group: 'github']
issue-reopen number:
    gh issue reopen {{number}} -R {{github_repo}}

# Create a label if it doesn't exist (color optional, default blue)
[group: 'github']
label-create name color="0075ca":
    #!/usr/bin/env bash
    set -euo pipefail
    NAME={{quote(name)}}
    COLOR=$(echo {{quote(color)}} | tr -d '#')
    if gh label list -R {{github_repo}} --limit 200 --json name --jq '.[].name' | grep -qxF "$NAME"; then
        echo "✓ Label '$NAME' already exists"
    else
        gh label create "$NAME" -R {{github_repo}} --color "$COLOR"
        echo "✓ Label '$NAME' created"
    fi

# Add labels to issue (space-separated label names)
[group: 'github']
issue-label number *labels:
    #!/usr/bin/env bash
    set -euo pipefail
    for label in {{labels}}; do
        gh issue edit {{number}} -R {{github_repo}} --add-label "$label"
        echo "✓ Label '$label' added to issue #{{number}}"
    done

# Create a label (if missing, with random color) and assign it to an issue
[group: 'github']
issue-label-create number name:
    #!/usr/bin/env bash
    set -euo pipefail
    COLORS=("e11d48" "ea580c" "d97706" "65a30d" "16a34a" "059669" "0891b2" "2563eb" "7c3aed" "c026d3" \
            "be185d" "b45309" "4d7c0f" "0e7490" "1d4ed8" "6d28d9" "a21caf" "be123c" "15803d" "0369a1")
    RANDOM_COLOR=${COLORS[$((RANDOM % ${#COLORS[@]}))]}
    NAME={{quote(name)}}
    if gh label list -R {{github_repo}} --limit 200 --json name --jq '.[].name' | grep -qxF "$NAME"; then
        echo "✓ Label '$NAME' already exists"
    else
        gh label create "$NAME" -R {{github_repo}} --color "$RANDOM_COLOR"
        echo "✓ Label '$NAME' created with color #${RANDOM_COLOR}"
    fi
    gh issue edit {{number}} -R {{github_repo}} --add-label "$NAME"
    echo "✓ Label assigned to issue #{{number}}"

# Create new issue (body optional)
[group: 'github']
issue-create title body="":
    #!/usr/bin/env bash
    set -euo pipefail
    BODY={{quote(body)}}
    if [ -z "$BODY" ]; then
        gh issue create -R {{github_repo}} --title {{quote(title)}} --body ""
    else
        gh issue create -R {{github_repo}} --title {{quote(title)}} --body "$BODY"
    fi

# Create new issue with body read from a file
[group: 'github']
issue-create-file title file:
    gh issue create -R {{github_repo}} --title {{quote(title)}} --body-file {{quote(file)}}

# Edit issue body from file (usage: just issue-edit-body 42 /path/to/body.md)
[group: 'github']
issue-edit-body number file:
    gh issue edit {{number}} -R {{github_repo}} --body-file {{quote(file)}}

# Create a pull request from current branch to main
[group: 'github']
pr-create title body="" base="main":
    gh pr create -R {{github_repo}} --title {{quote(title)}} --body {{quote(body)}} --base {{base}} --head "$(git branch --show-current)"

# ============================================================================
# GitHub Releases
# ============================================================================

# List all releases
[group: 'github']
release-list:
    gh release list -R {{github_repo}} --limit 50

# Show release details
[group: 'github']
release-show tag:
    gh release view "{{tag}}" -R {{github_repo}}

# Create a new release (creates tag, pushes main+tag, creates GitHub release via gh)
# Pass notes_file to use custom rich notes; omit for auto-generated notes from commits
[group: 'github']
release-create tag previous_tag="" notes_file="" draft="false" prerelease="false":
    #!/usr/bin/env bash
    set -euo pipefail

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
            echo "https://github.com/{{github_repo}}/compare/${PREV_TAG}...{{tag}}"
        } > "$NOTES_FILE"
    fi

    # Create release via gh
    echo "🚀 Creating release on GitHub..."
    EXTRA=""
    if [ "{{draft}}" = "true" ]; then EXTRA="$EXTRA --draft"; fi
    if [ "{{prerelease}}" = "true" ]; then EXTRA="$EXTRA --prerelease"; fi
    gh release create "{{tag}}" -R {{github_repo}} --title "{{tag}}" --notes-file "$NOTES_FILE" $EXTRA
    echo ""
    echo "✓ Release {{tag}} created!"

# Delete a release (use with caution!)
[group: 'github']
release-delete tag:
    gh release delete "{{tag}}" -R {{github_repo}} --yes

# ============================================================================
# Tasks
# ============================================================================

# List ready tasks
[group: 'tasks']
tasks:
    taskdb list --status ready

# List tasks by status (draft|ready|in-progress|complete)
[group: 'tasks']
tasks-status status:
    taskdb list --status {{status}}

# Show a task
[group: 'tasks']
task number:
    taskdb view {{number}}

# Create a new task
[group: 'tasks']
task-create title description="":
    taskdb create {{quote(title)}} --description {{quote(description)}}

# Mark a task as complete
[group: 'tasks']
task-complete number:
    taskdb complete {{number}}
