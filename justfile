
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
    uv run python manage.py tailwind runserver


# Install requirements
requirements:
    uv sync

# Update all packages
update_all:
    uv sync --upgrade

# Update a specific package
update package:
    uv sync --upgrade-package {{package}}

# Run database migrations
migrate:
    python manage.py migrate --settings=core.settings.development

# Run tests
test:
    COVERAGE_CORE=sysmon python -m pytest --reuse-db -s

# Run fast tests
ftest:
    pytest -n 8 --reuse-db

lint:
    uv run ruff check --fix --unsafe-fixes .
    uv run ruff format .
    just _pre-commit run --all-files

_pre-commit *args:
    uvx --with pre-commit-uv pre-commit {{ args }}

secure:
    uv-secure

docker_up:
    docker compose up -d

docker_build:
    docker compose up -d --build

docker_down:
    docker compose down -v
