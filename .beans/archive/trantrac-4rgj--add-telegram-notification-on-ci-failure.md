---
# trantrac-4rgj
title: Add Telegram notification on CI failure
status: completed
type: task
priority: normal
created_at: 2026-02-26T14:54:00Z
updated_at: 2026-02-27T14:27:21Z
---

Configure Woodpecker CI to send a Telegram message when the pipeline fails. Use curl to call the Telegram Bot API.

## Summary of Changes\n\nAdded Telegram notification on CI failure via Woodpecker pipeline. Added push event filter and parallel test support. Fix #76.
