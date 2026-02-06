---
# trantrac-949v
title: Move Google Sheets config to Django admin settings page
status: completed
type: feature
priority: normal
created_at: 2026-02-06T07:55:20Z
updated_at: 2026-02-06T08:09:04Z
---

Move Google Sheets credentials from environment variables to Django admin settings page for better management and UX.

## Checklist
- [x] Analyze current Google Sheets configuration in settings
- [x] Create a model to store Google Sheets settings
- [x] Create admin interface for the settings
- [x] Update trantrac/utils.py to use DB settings instead of env vars
- [x] Test the integration with Google Sheets
- [x] Update documentation
