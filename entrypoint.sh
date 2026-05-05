#!/bin/sh

set -eu

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
