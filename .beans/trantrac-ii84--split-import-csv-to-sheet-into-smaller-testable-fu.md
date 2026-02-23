---
# trantrac-ii84
title: Split import_csv_to_sheet into smaller testable functions
status: todo
type: task
priority: high
created_at: 2026-02-22T19:54:12Z
updated_at: 2026-02-22T19:54:12Z
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

- [ ] Extract `validate_csv_columns()`
- [ ] Extract `parse_csv_transactions()`
- [ ] Extract `ensure_categories_exist()`
- [ ] Extract `ensure_subcategories_exist()`
- [ ] Extract `save_transactions_to_sheets()`
- [ ] Update main function to orchestrate
- [ ] Add unit tests for each function
- [ ] Update integration tests

## Benefits

- Easier to test individual pieces
- Better code reusability
- Improved maintainability
- Clearer separation of concerns
