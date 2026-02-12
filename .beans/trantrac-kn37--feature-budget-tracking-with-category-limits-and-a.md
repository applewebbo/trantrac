---
# trantrac-kn37
title: 'Feature: budget tracking with category limits and alerts'
status: todo
type: feature
priority: normal
created_at: 2026-02-11T20:48:33Z
updated_at: 2026-02-11T20:48:33Z
---

## Plan

### 1. Budget model (trantrac/models.py)
- New model:
  - category (FK to Category)
  - month / year fields
  - limit (DecimalField)
  - alert_threshold (IntegerField, default=80%)
- Unique constraint on (category, month, year)

### 2. Budget management views
- CRUD views for budgets (HTMX-powered)
- Budget setup page: set limits per category per month
- Copy budgets from previous month

### 3. Budget tracking
- Compare actual spending (from Sheets data) vs budget limits
- Show progress bars per category
- Alert when threshold exceeded (on-page notification)
- Optional: Telegram alert on budget exceed

### 4. Files to create/modify
- Modify `trantrac/models.py` — Budget model
- Create migration
- Create `templates/trantrac/budgets.html`
- Modify `trantrac/views.py` — budget views
- Modify `trantrac/urls.py` — routes
- Modify navbar — add link

## Todo
- [ ] Create Budget model and migration
- [ ] Create budget CRUD views (HTMX)
- [ ] Create budget template with progress bars
- [ ] Implement spending vs budget comparison
- [ ] Add budget alerts (on-page)
- [ ] Add copy-from-previous-month feature
- [ ] Add tests
