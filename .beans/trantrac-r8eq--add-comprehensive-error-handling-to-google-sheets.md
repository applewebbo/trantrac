---
# trantrac-r8eq
title: Add comprehensive error handling to Google Sheets API calls
status: in-progress
type: bug
priority: critical
created_at: 2026-02-22T19:53:07Z
updated_at: 2026-02-22T20:02:07Z
parent: trantrac-zm6a
---

## Problem

Google Sheets API calls lack proper error handling, causing crashes and data inconsistency.

## Affected Files

- `trantrac/utils.py`: `save_to_sheet()`, `get_sheets_service()`, `import_csv_to_sheet()`
- `trantrac/models.py`: `save_category_and_sub_to_sheet()`, `Subcategory.save()`
- `trantrac/views.py`: All views calling Sheets functions

## Tasks

- [ ] Add try/except for HttpError in `save_to_sheet()`
- [ ] Return tuple (success: bool, message: str) instead of bool
- [ ] Add logging for all API errors
- [ ] Wrap API calls in views with try/except
- [ ] Handle partial failures in `import_csv_to_sheet()`
- [ ] Add error recovery in `Subcategory.save()`

## Expected Behavior

- API errors should be logged
- Users see friendly error messages
- Database remains consistent even if Sheets sync fails
- Return structured error information for debugging
