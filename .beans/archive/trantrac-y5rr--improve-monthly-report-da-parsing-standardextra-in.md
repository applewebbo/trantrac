---
# trantrac-y5rr
title: 'Improve monthly report: DA parsing + standard/extra income + detailed expenses'
status: completed
type: feature
priority: normal
created_at: 2026-05-05T07:41:29Z
updated_at: 2026-05-05T08:05:42Z
---

Issue #87: 3 features for monthly PDF report quality improvement

## Summary of Changes

- Added IncomeParsingConfig singleton model: enable/disable DA-string parsing from admin, configurable trigger string
- Added StandardIncomeKeyword model: manage standard income keywords from admin
- Migration 0010: creates both new models
- Admin: both models registered under a new 'Report' section (custom get_app_list override)
- reports.py: added extract_da_label, is_standard_income, build_income_by_user, build_expenses_by_category
- get_monthly_report_data now reads config from DB and returns structured income/expenses dicts
- Template: income section shows user header + Standard/Extra subsections with individual rows; expenses section shows category header + individual transactions
- 32 new tests, 100% coverage maintained
