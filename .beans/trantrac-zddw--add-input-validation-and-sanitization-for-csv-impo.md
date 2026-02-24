---
# trantrac-zddw
title: Add input validation and sanitization for CSV imports
status: completed
type: bug
priority: high
created_at: 2026-02-22T19:54:40Z
updated_at: 2026-02-24T06:49:51Z
parent: trantrac-zm6a
---

## Problem

CSV content not validated or sanitized, risking injection attacks and data corruption.

## Location

`trantrac/utils.py:95-196`

## Missing Validations

- No data type validation
- No text sanitization
- No length limits on category/subcategory names
- No protection against CSV formula injection

## Tasks

- [x] Validate amount is numeric and within reasonable range
- [x] Validate dates are valid dates
- [x] Strip dangerous characters (=, +, @) from start of descriptions
- [x] Enforce max length on category names (matching model max_length)
- [x] Enforce max length on subcategory names
- [x] Sanitize description text
- [x] Add validation for user names
- [x] Return detailed validation errors to user

## CSV Formula Injection Prevention

```python
def sanitize_csv_value(value: str) -> str:
    """Remove dangerous characters that could trigger formula execution"""
    if value and value[0] in ('=', '+', '-', '@'):
        return "'" + value  # Prefix with single quote
    return value
```

## Additional Security

- Validate against expected data types
- Add max amount limit (e.g., 1,000,000€)
- Log suspicious patterns

## Summary of Changes

Added sanitize_csv_value() to strip leading formula-injection chars (=, +, @). Added date format validation, amount range check (max 1M). Applied sanitization + max_length truncation to category/subcategory names. 11 new tests, 100% coverage.
