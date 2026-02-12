---
# trantrac-pkve
title: 'Monthly PDF Reports: Web Interface'
status: completed
type: feature
priority: normal
created_at: 2026-02-10T12:25:30Z
updated_at: 2026-02-10T12:35:25Z
---

Web interface for listing and downloading monthly PDF reports (issue #43). Views, templates, URLs, admin, navbar.

## Summary of Changes

- Added `reports_list` and `download_report` views in `trantrac/views.py`
- Added URL patterns for `/reports/` and `/reports/<year>/<month>/download/`
- Created `templates/trantrac/reports_list.html` with DaisyUI table and empty state
- Registered `MonthlyReport` in admin with readonly fields and filters
- Added `month_name` property to `MonthlyReport` model
- Added Report link in navbar (desktop + mobile) after Importa Transazioni
- 258 tests passing, 100% coverage
