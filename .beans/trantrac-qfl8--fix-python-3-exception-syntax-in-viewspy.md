---
# trantrac-qfl8
title: Fix Python 3 exception syntax in views.py
status: todo
type: bug
priority: critical
created_at: 2026-02-22T19:53:28Z
updated_at: 2026-02-22T19:53:28Z
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
