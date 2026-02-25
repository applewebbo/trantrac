---
# trantrac-qfl8
title: Fix Python 3 exception syntax in views.py
status: scrapped
type: bug
priority: critical
created_at: 2026-02-22T19:53:28Z
updated_at: 2026-02-23T14:57:09Z
parent: trantrac-zm6a
---

## Problem

Invalid Python 2 exception syntax used in views.py line 234

## Location

`trantrac/views.py:234`

## Current Code

```python
except MonthlyReport.DoesNotExist, TypeError, ValueError:
```

## Fix Required

```python
except (MonthlyReport.DoesNotExist, TypeError, ValueError):
```

## Tasks

- [ ] Fix exception syntax
- [ ] Search for other instances of old syntax
- [ ] Add test to verify exception handling works correctly

## Summary of Changes\n\n- Fixed Python 3 exception syntax:  → \n- All 375 tests pass, coverage 100%

## Reasons for Scrapping

The 'old Python 2 syntax'  is actually valid Python 3 syntax.
Python 3.14 AST parses it as a tuple of exception types (all three are caught).
ruff format explicitly REMOVES parentheses as unnecessary in this form.
No fix needed — the code is correct and ruff-preferred.
