---
# trantrac-v2k7
title: Fix generate_monthly_report cron failing with exit code 2 in Coolify
status: completed
type: bug
priority: normal
created_at: 2026-06-02T06:33:52Z
updated_at: 2026-06-02T06:35:25Z
---

sys.exit(2) used as skip signal (report exists or no transactions) is treated as failure by Coolify cron. Replace with return.

## Summary of Changes\n\nReplaced sys.exit(2) with return in two skip conditions:\n- Report already exists (no --force)\n- No transactions found for the month\n\nExit code 2 was treated as failure by Coolify cron. These are normal skip conditions, not errors. Tests updated accordingly.
