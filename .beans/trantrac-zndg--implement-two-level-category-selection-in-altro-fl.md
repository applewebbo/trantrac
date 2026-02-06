---
# trantrac-zndg
title: 'Implement two-level category selection in ''Altro'' flow for #40'
status: completed
type: feature
priority: normal
created_at: 2026-02-06T16:06:45Z
updated_at: 2026-02-06T16:10:53Z
---

Modify the Telegram bot 'Altro' flow to show categories first, then subcategories.

## Implementation plan:

1. **Rename/refactor `show_all_subcategories`** → `show_all_categories`
   - Show numbered list of all categories
   - Store categories in context
   - Update state to `awaiting_category_selection`

2. **Add new function `show_category_subcategories`**
   - Accept category_id parameter
   - Show all subcategories for the selected category
   - Update state to `awaiting_subcategory_selection`

3. **Update `handle_subcategory_selection`**
   - Add state check for `awaiting_category_selection`
   - If selecting category: call `show_category_subcategories`
   - If selecting subcategory: proceed with confirmation (existing logic)

4. **Update context state management**
   - Add `awaiting_category_selection` state
   - Store selected category in context

## Files to modify:
- `telegram_bot/handlers/transaction.py`

## Testing:
- Update existing tests
- Add tests for new flow
- Maintain 100% coverage

## Target branch: 2026.2
