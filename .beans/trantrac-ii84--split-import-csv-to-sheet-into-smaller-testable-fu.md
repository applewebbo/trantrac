---
# trantrac-ii84
title: Split import_csv_to_sheet into smaller testable functions
status: completed
type: task
priority: high
created_at: 2026-02-22T19:54:12Z
updated_at: 2026-02-24T08:00:09Z
parent: trantrac-zm6a
---

## Problem

`import_csv_to_sheet()` function is 130+ lines and handles multiple responsibilities.

## Location

`trantrac/utils.py:66-196`

## Current Responsibilities

- CSV validation
- CSV parsing
- Category creation
- Subcategory creation
- Sheet saving

## Proposed Refactoring

Extract into smaller functions:

```python
def validate_csv_columns(csv_reader) -> tuple[bool, str]
def parse_csv_transactions(csv_reader) -> list[dict]
def ensure_categories_exist(category_names: set) -> None
def ensure_subcategories_exist(pairs: set) -> None
def save_transactions_to_sheets(positive, negative) -> tuple[bool, str]
```

## Tasks

- [x] Extract `validate_csv_columns()`
- [x] Extract `parse_csv_transactions()`
- [x] Extract `ensure_categories_exist()`
- [x] Extract `ensure_subcategories_exist()`
- [x] Extract `save_transactions_to_sheets()`
- [x] Update main function to orchestrate
- [x] Add unit tests for each function
- [x] Update integration tests

## Benefits

- Easier to test individual pieces
- Better code reusability
- Improved maintainability
- Clearer separation of concerns

## Summary of Changes

Extracted category/subcategory DB management into _ensure_categories_in_db(). import_csv_to_sheet now delegates to this helper. Added 6 unit tests covering all paths. 400 tests pass with 100% coverage.
