---
# trantrac-32dm
title: Remove side effects from Subcategory.save() using signals
status: completed
type: task
priority: high
created_at: 2026-02-22T19:54:26Z
updated_at: 2026-02-24T07:14:12Z
parent: trantrac-zm6a
---

## Problem

`Subcategory.save()` directly calls Google Sheets API, creating tight coupling and making testing difficult.

## Location

`trantrac/models.py:50-57`

## Current Code

```python
def save(self, *args, **kwargs):
    if not self.skip_sheet_save:
        values = [[self.category.name, self.name]]
        save_category_and_sub_to_sheet(values)
        pass  # <- Remove this
    super().save(*args, **kwargs)
```

## Issues

- Violates single responsibility principle
- Hard to test
- Can't save subcategory without Sheets access
- Database transaction not atomic with Sheets sync

## Solution

Use Django signals for decoupled sync:

```python
# In models.py
@receiver(post_save, sender=Subcategory)
def sync_subcategory_to_sheets(sender, instance, created, **kwargs):
    if created and not getattr(instance, 'skip_sheet_save', False):
        try:
            values = [[instance.category.name, instance.name]]
            save_category_and_sub_to_sheet(values)
        except Exception as e:
            logger.error(f"Failed to sync subcategory to sheets: {e}")
```

## Tasks

- [x] Create signal handler for post_save
- [x] Remove save() override from model
- [x] Add error handling in signal
- [x] Update tests to mock signal
- [x] Consider async task queue for better reliability (deferred)

## Summary of Changes

Replaced Subcategory.save() override with post_save signal handler sync_subcategory_to_sheets(). Signal only fires on created=True to avoid syncing updates. Error handling preserved in signal. All 394 tests pass.
