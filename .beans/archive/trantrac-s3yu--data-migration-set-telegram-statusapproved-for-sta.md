---
# trantrac-s3yu
title: 'Data migration: set telegram_status=approved for staff with telegram_chat_id'
status: completed
type: task
priority: normal
created_at: 2026-02-27T10:00:20Z
updated_at: 2026-02-27T10:03:02Z
---

Create a Django data migration that automatically sets telegram_status='approved' for all staff users (is_staff=True) who already have a telegram_chat_id set but telegram_status is NULL. This fixes the issue where existing admin users don't receive enrollment notifications.

## Summary of Changes

- Created
- Sets  for all staff users with  set but
- Reverse migration is noop (safe to roll back without data loss)
- All 475 tests pass
