---
# trantrac-wznj
title: 'Simplify BOT flow - show only subcategory names for #37'
status: in-progress
type: task
created_at: 2026-02-06T15:28:35Z
updated_at: 2026-02-06T15:28:35Z
---

Simplify the Telegram bot flow by showing only subcategory names (without 'Category > Subcategory') in the selection lists.

## Changes needed:

1. **Initial 5 suggestions** (transaction.py:126): Show only subcategory name
2. **Paginated 'all' list** (transaction.py:249): Show only subcategory name
3. **Success message** (transaction_service.py:79): Keep 'Category > Subcategory' format (NO CHANGES)

## Implementation:

- Remove `{subcat.category.name} >` from both suggestion displays
- Keep the confirmation message unchanged
- Run tests to ensure functionality works
- Target branch: 2026.2
