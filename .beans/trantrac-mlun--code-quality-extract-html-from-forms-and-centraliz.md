---
# trantrac-mlun
title: 'Code quality: extract HTML from forms and centralize date parsing'
status: todo
type: task
priority: low
created_at: 2026-02-11T20:48:51Z
updated_at: 2026-02-11T20:48:51Z
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
- [ ] Create template partials for form buttons
- [ ] Refactor forms.py to use template partials
- [ ] Create date_utils.py with parse_date()
- [ ] Replace date parsing in utils.py
- [ ] Replace date parsing in reports.py
- [ ] Replace date parsing in parser.py
- [ ] Add tests for parse_date()
