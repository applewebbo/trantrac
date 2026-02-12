---
# trantrac-mlun
title: 'Code quality: extract HTML from forms and centralize date parsing'
status: completed
type: task
priority: low
created_at: 2026-02-11T20:48:51Z
updated_at: 2026-02-12T14:04:53Z
---

## Plan

### 1. Extract inline HTML from forms.py
- Move HTML_ADD_BUTTON and similar inline HTML to template partials
- Create `templates/includes/add_category_button.html`
- Create `templates/includes/add_subcategory_button.html`
- Use crispy-forms Layout with {% include %} or Div with template

### 2. Centralize date parsing
- Create `trantrac/date_utils.py` with unified `parse_date()` function
- Handle formats: YYYY-MM-DD, DD/MM/YYYY, DD/MM/YY
- Replace duplicate parsing in:
  - `trantrac/utils.py:102-104`
  - `trantrac/reports.py:19-36`
  - `telegram_bot/services/parser.py`

## Todo
- [x] Create template partials for form buttons
- [x] Refactor forms.py to use template partials
- [x] Create date_utils.py with parse_date()
- [x] Replace date parsing in utils.py
- [x] Replace date parsing in reports.py
- [x] Replace date parsing in parser.py
- [x] Add tests for parse_date()

## Summary of Changes

- Extracted 4 inline HTML blocks from forms.py to template partials in templates/includes/
- Created: add_category_button.html, add_subcategory_button.html, quick_categories_start.html, quick_categories_end.html
- Replaced forms.py string constants with {% include %} references
- Created trantrac/date_utils.py with parse_date() centralizing date parsing logic
- Updated reports.py to import parse_date from date_utils (re-exported as parse_italian_date for backward compat)
- Added tests/trantrac/test_date_utils.py with 11 tests for parse_date()
- All 305 tests pass with 100% coverage
