---
# trantrac-cx4r
title: 'Security hardening: configurable user names, production headers, env validation'
status: completed
type: task
priority: high
created_at: 2026-02-11T20:47:52Z
updated_at: 2026-02-12T06:48:23Z
---

## Plan

### 1. Replace hardcoded user names in CSV import (utils.py:113-119)
- Create a `UserMapping` model or use env-based config to map keywords → users
- Remove hardcoded "VIVIANA", "ENRICO", "APPLE" strings
- Allow configuration via Django admin

### 2. Add production security headers (core/settings.py)
In the `if env("PRODUCTION"):` block, add:
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_HSTS_SECONDS = 31536000`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True`

### 3. Validate required env vars on startup
Add validation in settings.py for PRODUCTION mode:
- Check TELEGRAM_BOT_TOKEN, GOOGLE_SHEETS_SPREADSHEET_ID, MAILGUN_API_KEY, SECRET_KEY
- Raise `ImproperlyConfigured` if missing

### 4. Fix except syntax (views.py:258)
- `except MonthlyReport.DoesNotExist, TypeError, ValueError:` → `except (MonthlyReport.DoesNotExist, TypeError, ValueError):`

## Todo
- [x] Fix except syntax in views.py
- [x] Add production security headers
- [x] Add env var validation on startup
- [x] Make user name mapping configurable
- [x] Add tests for all changes

## Summary of Changes

- Fixed  tuple syntax in
- Added production security headers (HSTS, secure cookies, SSL redirect) in
- Added required env var validation on startup for PRODUCTION mode
- Created  model to replace hardcoded user names in CSV import
- Registered  in Django admin with configurable keyword/display_name/order
- Created migration
- Updated test to use  DB fixtures instead of hardcoded strings
- Fixed  (unclosed PDF file handles in streaming response tests)
- Removed unknown  rule  from
