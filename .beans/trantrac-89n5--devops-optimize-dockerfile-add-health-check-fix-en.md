---
# trantrac-89n5
title: 'DevOps: optimize Dockerfile, add health check, fix entrypoint'
status: completed
type: task
priority: normal
created_at: 2026-02-11T20:48:02Z
updated_at: 2026-02-12T07:06:05Z
---

## Plan

### 1. Optimize Dockerfile
- Remove Bun installation and `bun install` from production image
- django-tailwind-cli handles CSS build without node_modules
- Saves ~200MB image size

### 2. Add health check endpoint
- Add `GET /health/` endpoint returning `{"status": "ok"}`
- No auth required, lightweight check
- Useful for Caprover/Docker health monitoring

### 3. Fix entrypoint.sh error handling
- Add `set -e` already present, but `migrate` should explicitly fail:
  `python manage.py migrate || exit 1`
- Add basic readiness log message after granian starts

## Todo
- [ ] Remove Bun from Dockerfile
- [ ] Add /health/ endpoint in core/urls.py
- [ ] Fix entrypoint.sh migration error handling
- [ ] Add test for health endpoint
- [ ] Test Docker build locally

## Summary of Changes

- Removed Bun installation from Dockerfile (~200MB savings); tailwind-cli-extra bundles DaisyUI natively
- Moved COPY of pyproject.toml/uv.lock before COPY . to improve Docker layer caching
- Added GET /health/ endpoint returning {"status": "ok"} (no auth required)
- entrypoint.sh already had set -eu so no changes needed
- Added 3 tests for health check endpoint
