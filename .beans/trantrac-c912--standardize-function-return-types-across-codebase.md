---
# trantrac-c912
title: Standardize function return types across codebase
status: todo
type: task
priority: high
created_at: 2026-02-22T19:55:08Z
updated_at: 2026-02-22T19:55:08Z
parent: trantrac-zm6a
---

## Problem

Inconsistent return types across similar functions make error handling unpredictable.

## Current Inconsistencies

- `import_csv_to_sheet()` returns `(bool, str)`
- `save_to_sheet()` returns `bool`
- `delete_bot_transaction()` returns `(bool, str)`
- `create_transaction()` returns `(bool, str)`

## Recommendation

Standardize on tuple returns: `(success: bool, message: str)` for all functions that can fail.

## Affected Functions

### utils.py
- `save_to_sheet()` - currently returns bool
- `get_sheets_service()` - currently returns service or None
- `get_spreadsheet_id()` - currently returns str or None

### Services
- All transaction service functions

## Tasks

- [ ] Update `save_to_sheet()` to return `(bool, str)`
- [ ] Update `get_sheets_service()` to return `(service|None, error_msg)`
- [ ] Update calling code to handle tuple returns
- [ ] Add type hints to all function signatures
- [ ] Update tests to verify new return types
- [ ] Document return type convention in CLAUDE.md

## Example Refactor

```python
# Before
def save_to_sheet(values, sheet_name) -> bool:
    ...

# After
def save_to_sheet(values, sheet_name) -> tuple[bool, str]:
    try:
        ...
        return True, "Saved successfully"
    except HttpError as e:
        return False, f"API error: {e.reason}"
```
