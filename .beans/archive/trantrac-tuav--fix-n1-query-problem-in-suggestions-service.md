---
# trantrac-tuav
title: Fix N+1 query problem in suggestions service
status: completed
type: bug
priority: critical
created_at: 2026-02-22T19:54:00Z
updated_at: 2026-02-23T15:00:07Z
parent: trantrac-zm6a
---

## Problem

N+1 query problem in suggestion service causes performance degradation.

## Location

`telegram_bot/services/suggestions.py:36-47`

## Current Code

```python
for item in recent_usage:
    subcategory = Subcategory.objects.select_related("category").get(
        id=item["subcategory"]
    )
```

## Issue

Each loop iteration makes a separate DB query (N queries for N items).

## Solution

```python
# Fetch all IDs first
subcategory_ids = [item["subcategory"] for item in recent_usage]

# Bulk fetch with single query
subcategories = Subcategory.objects.select_related("category").filter(
    id__in=subcategory_ids
)

# Create mapping
subcat_map = {s.id: s for s in subcategories}

# Use mapping
for item in recent_usage:
    subcategory = subcat_map[item["subcategory"]]
```

## Tasks

- [ ] Refactor to use bulk query with `filter(id__in=...)`
- [ ] Create ID-to-object mapping
- [ ] Update tests to verify single query
- [ ] Measure performance improvement
