---
# trantrac-pfds
title: 'Monthly PDF Reports: Core Infrastructure'
status: completed
type: feature
priority: normal
created_at: 2026-02-10T11:56:57Z
updated_at: 2026-02-10T12:19:42Z
---

Implement core infrastructure for generating monthly PDF reports from Google Sheets data (issue #42). Phase 1: Data layer + MonthlyReport model. Phase 2: PDF generation. Phase 3: Storage & Security.

## Summary of Changes

- Added `MonthlyReport` model to `trantrac/models.py` with UUID-based file storage
- Created migration `0004_monthlyreport.py`
- Created `trantrac/reports.py`: pure functions for data fetching/aggregation from Google Sheets
- Created `trantrac/pdf_generator.py`: WeasyPrint-based PDF generation pipeline
- Created `templates/trantrac/reports/monthly_report.html`: PDF template with inline CSS
- Added weasyprint and pillow dependencies (pyproject.toml / uv.lock)
- Added DYLD_LIBRARY_PATH to justfile test commands (macOS)
- Added WeasyPrint system libs to Dockerfile (libpango, libgdk-pixbuf2.0, etc.)
- 249 tests passing, 100% coverage
