---
# trantrac-4zqs
title: 'Smart Categorization: Add UserKeywordPreference model for learning'
status: completed
type: task
priority: normal
created_at: 2026-02-24T07:08:15Z
updated_at: 2026-02-26T11:02:02Z
parent: trantrac-iv16
---

## Target Release\n\n2026.6

## Plan\n\n- [x] Add UserKeywordPreference model (user, keyword, category FK, subcategory FK, count)\n- [x] Register in admin\n- [x] Add signal/hook to auto-extract first significant word when CategoryUsage is created\n- [x] Italian stopwords list for filtering in categorization.py\n- [x] Create migration

## Summary of Changes\n\nAdded UserKeywordPreference model (user, keyword, category, subcategory, count). Registered in admin. Added post_save signal on CategoryUsage that auto-extracts first significant word and creates/increments UserKeywordPreference. Added CategoryUsage.description field to carry description context to signal.
