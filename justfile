
# Define the default recipe
default:
    @just --list

# Bootstrap the project (UV and BUN needed)
bootstrap:
    uv venv
    source .venv/bin/activate
    uv sync
    bun add -D daisyui@beta

# Run the local development server
local:
    uv run python manage.py tailwind runserver --force-default-runserver


# Install requirements
requirements:
    uv sync

# Update all packages
@update_all: lock
    uv sync --all-extras --upgrade
    uvx --with pre-commit-uv prek auto-update

@lock:
    echo "Rebuilding lock file..."
    uv lock --upgrade
    echo "Done!"

# Update a specific package
update package:
    uv sync --upgrade-package {{package}}

# Run database migrations
migrate:
    python manage.py migrate --settings=core.settings.development

# Run tests with coverage
test:
    uv run pytest tests/

# Run fast parallel tests
ftest:
    uv run pytest tests/ -n 8 --reuse-db --no-cov

# Run tests with coverage report
test-cov:
    uv run pytest tests/ --cov --cov-report=html --cov-report=term-missing

lint:
    uv run ruff check --fix --unsafe-fixes .
    uv run ruff format .
    just _pre-commit run --all-files

_pre-commit *args:
    uvx prek {{ args }}

secure:
    uv-secure

docker_up:
    docker compose up -d

docker_build:
    docker compose up -d --build

docker_down:
    docker compose down -v

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
