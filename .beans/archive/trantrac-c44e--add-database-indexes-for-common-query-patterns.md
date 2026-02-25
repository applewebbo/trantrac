---
# trantrac-c44e
title: Add database indexes for common query patterns
status: completed
type: task
priority: high
created_at: 2026-02-22T19:54:53Z
updated_at: 2026-02-24T07:05:51Z
parent: trantrac-zm6a
---

## Problem

Missing database indexes on frequently queried fields causing slow queries.

## Affected Models

### CategoryUsage

`trantrac/models.py:123-129`

Current indexes:
```python
indexes = [
    models.Index(fields=["-created_at"]),
    models.Index(fields=["category", "subcategory"]),
    models.Index(fields=["user", "-created_at"]),
]
```

Missing: Composite index for common query pattern `filter(user=user, created_at__gte=cutoff)`

### User Model

`users/models.py`

`telegram_chat_id` used in lookups but only has unique constraint.

## Tasks

- [x] Add composite index to CategoryUsage: `["user", "-created_at", "subcategory"]`
- [x] Document that unique=True on telegram_chat_id creates index
- [x] Run `makemigrations` to create migration
- [x] Test query performance before/after
- [x] Consider adding index on BotTransaction.telegram_message_id (not needed, no direct lookups)

## Migration

```python
migrations.AddIndex(
    model_name='categoryusage',
    index=models.Index(
        fields=['user', '-created_at', 'subcategory'],
        name='idx_usage_user_date_sub'
    ),
)
```

## Summary of Changes

Added covering index `idx_usage_user_date_sub` on CategoryUsage(user, -created_at, subcategory) to optimize the suggestions query pattern. Migration 0008 created and applied. telegram_chat_id already indexed via unique=True constraint.
