---
# trantrac-b444
title: 'Performance: cache GoogleSheetsSettings and add database indexes'
status: todo
type: task
priority: normal
created_at: 2026-02-11T20:47:57Z
updated_at: 2026-02-11T20:47:57Z
---

## Plan

### 1. Cache GoogleSheetsSettings (trantrac/models.py)
- Add Django cache to `get_settings()` classmethod
- Cache for 1 hour, invalidate on save via `post_save` signal
- Avoids repeated `get_or_create` on every sheets operation

### 2. Add database indexes (trantrac/models.py)
- `Category.name` → `db_index=True`
- `Subcategory.name` → `db_index=True`
- `CategoryUsage` → compound index on `(user, -created_at)`
- Create migration

## Todo
- [ ] Add caching to GoogleSheetsSettings.get_settings()
- [ ] Add cache invalidation on model save
- [ ] Add db_index to Category.name and Subcategory.name
- [ ] Add compound index to CategoryUsage
- [ ] Create and test migration
- [ ] Add tests for caching behavior
