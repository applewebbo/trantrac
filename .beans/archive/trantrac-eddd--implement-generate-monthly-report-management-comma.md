---
# trantrac-eddd
title: 'Implement generate_monthly_report management command for #44'
status: completed
type: task
priority: normal
created_at: 2026-02-11T13:54:48Z
updated_at: 2026-02-11T13:57:59Z
---

Create Django management command for automatic monthly PDF report generation (issue #44).

## Tasks
- [x] Create management command file at trantrac/management/commands/generate_monthly_report.py
- [x] Implement --year, --month, --force, --dry-run options
- [x] Auto-detect previous month when no year/month specified
- [x] Check if report already exists (skip unless --force)
- [x] Skip if no transactions found
- [x] Proper exit codes: 0 (success), 1 (error), 2 (skipped/no transactions)
- [x] Logging with Django logger
- [x] Write tests in tests/trantrac/test_management_commands.py
- [x] 100% test coverage

## Summary of Changes
Created management command generate_monthly_report with full test coverage (278 tests passing, 100% coverage).
