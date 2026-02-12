---
# trantrac-eeoc
title: 'Add back navigation and category info for issue #40'
status: completed
type: task
priority: normal
created_at: 2026-02-08T11:42:47Z
updated_at: 2026-02-08T11:45:56Z
---

Implement remaining features for two-level category selection:
- [x] Add back to categories button in subcategory page
- [x] Show category/subcategory in suggested subcategories page

## Summary of Changes

Implemented navigation improvements for issue #40:

1. **Category/Subcategory display in suggestions**: Modified `handle_transaction_message` to show category info alongside subcategory names (e.g., 'Alimentari > Spesa')

2. **Back to categories button**: Added '0. Torna alle categorie' option in subcategory pages when navigating from category selection
   - Stores `selected_category_id` in context to track navigation state
   - Updated `handle_subcategory_selection` to detect back navigation and clear category state

Files modified:
- `telegram_bot/handlers/transaction.py`
