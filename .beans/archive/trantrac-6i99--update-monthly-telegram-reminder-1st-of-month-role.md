---
# trantrac-6i99
title: 'Update monthly Telegram reminder: 1st of month + role-based messages'
status: completed
type: feature
priority: normal
created_at: 2026-05-05T06:46:41Z
updated_at: 2026-05-05T06:48:16Z
---

Issue #86: Change monthly check to 1st of month, add role-based messages (user vs admin), update cron from 28-31 to 1st

## Summary of Changes

- Changed monthly date check from last day of month to 1st of month
- Split monthly message into two roles:  (3 days to insert expenses) and  (import bank CSV by 5th)
- Admin message sent to users with  or
- Updated  help text and all tests to reflect new behavior
- Added 4 new tests covering role-based message logic
- Removed unused  import
