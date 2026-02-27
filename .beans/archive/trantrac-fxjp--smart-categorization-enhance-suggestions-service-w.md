---
# trantrac-fxjp
title: 'Smart Categorization: Enhance suggestions service with keyword learning and weighting'
status: completed
type: task
priority: normal
created_at: 2026-02-24T07:08:28Z
updated_at: 2026-02-26T11:02:11Z
parent: trantrac-iv16
blocked_by:
    - trantrac-4tio
    - trantrac-4zqs
---

## Target Release\n\n2026.6

## Plan\n\n- [x] Create suggestion service function (priority: UserKeywordPreference > MerchantMapping)\n- [x] Add HTMX view suggest_categories endpoint\n- [x] Add URL route /suggest-categories/\n- [x] Update TransactionForm description field with hx-get trigger (400ms debounce)\n- [x] Add badge partial template includes/category_suggestions.html\n- [x] Integrate badge click to pre-fill category+subcategory fields

## Summary of Changes\n\nCreated trantrac/categorization.py with extract_first_significant_word() and get_category_suggestions(). Added suggest_categories HTMX view. Description field now triggers suggestion fetch on keyup with 400ms debounce. Clicking a badge pre-fills category+subcategory selects.
