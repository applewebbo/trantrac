---
# trantrac-zddw
title: Add input validation and sanitization for CSV imports
status: todo
type: bug
priority: high
created_at: 2026-02-22T19:54:40Z
updated_at: 2026-02-22T19:54:40Z
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

- [ ] Validate amount is numeric and within reasonable range
- [ ] Validate dates are valid dates
- [ ] Strip dangerous characters (=, +, -, @) from start of descriptions
- [ ] Enforce max length on category names (matching model max_length)
- [ ] Enforce max length on subcategory names
- [ ] Sanitize description text
- [ ] Add validation for user names
- [ ] Return detailed validation errors to user

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
