#!/bin/sh

set -eu

echo "Building production css files..."
python manage.py tailwind build

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting granian..."
exec granian "core.asgi:application" \
    --host 0.0.0.0 \
    --port 80 \
    --interface asginl \
    --no-ws \
    --loop uvloop \
    --process-name "granian [core]" \
    --workers 1 \
    --backpressure 16
