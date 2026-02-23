---
# trantrac-zm6a
title: 'Release 2026.5.1: Code quality and performance improvements'
status: draft
type: milestone
created_at: 2026-02-22T19:51:46Z
updated_at: 2026-02-22T19:51:46Z
---

## Critical Fixes (Must Do)

- [ ] Add error handling to all Google Sheets API calls (utils.py, models.py, views.py)
- [ ] Fix Python 3 exception syntax in views.py line 234
- [ ] Add CSV file size validation (10MB limit)
- [ ] Fix N+1 query in suggestions service (telegram_bot/services/suggestions.py)
- [ ] Add try/except in view functions for graceful error handling

## High Priority (Should Do)

- [ ] Split import_csv_to_sheet() into smaller, testable functions
- [ ] Remove Subcategory.save() side effects, use Django signals instead
- [ ] Add input validation and sanitization for CSV content (prevent injection)
- [ ] Add database indexes for common query patterns
- [ ] Standardize return types across functions (bool, str) tuples

## Medium Priority (Nice to Have)

- [ ] Cache category/subcategory lists with invalidation
- [ ] Extract magic numbers to named constants
- [ ] Add comprehensive docstrings to all functions
- [ ] Remove deprecated show_all_subcategories() function
- [ ] Implement rate limiting on Telegram bot

## Low Priority (Future)

- [ ] Refactor to service layer architecture
- [ ] Add async task queue for Sheets operations (Celery)
- [ ] Add structured logging and monitoring
- [ ] Batch Google Sheets API calls for better performance
