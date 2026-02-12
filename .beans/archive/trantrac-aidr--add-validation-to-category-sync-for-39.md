---
# trantrac-aidr
title: 'Add validation to category sync for #39'
status: completed
type: feature
priority: normal
created_at: 2026-02-06T15:59:00Z
updated_at: 2026-02-06T16:05:43Z
---

Add validation and feedback to category synchronization from Google Sheets.

## Changes needed:

1. **Limit range or detect empty rows**: Stop reading when encountering empty rows
2. **Skip duplicates**: Track already-processed category/subcategory pairs
3. **Add feedback**: Report how many categories/subcategories were created/updated
4. **Error handling**: Handle malformed data gracefully

## Implementation:

- Modify `refresh_categories()` in `trantrac/views.py`
- Add deduplication logic
- Add counters for created/updated/skipped items
- Improve error messages

## Target branch: 2026.2
