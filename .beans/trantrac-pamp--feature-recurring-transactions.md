---
# trantrac-pamp
title: 'Feature: recurring transactions'
status: todo
type: feature
priority: low
created_at: 2026-02-11T20:48:46Z
updated_at: 2026-02-11T20:48:46Z
---

## Plan

### 1. RecurringTransaction model (trantrac/models.py)
- Fields:
  - user (FK to User)
  - description, amount, category, subcategory, account
  - frequency (monthly/weekly/yearly)
  - day_of_month (for monthly)
  - start_date, end_date (optional)
  - is_active (boolean)
  - last_generated (DateField)

### 2. Management command
- `generate_recurring_transactions` command
- Run daily via cron
- Check which transactions are due
- Create them via save_to_sheet()
- Update last_generated

### 3. Web interface
- CRUD for recurring transactions (HTMX)
- List of active recurring transactions
- Toggle active/inactive
- Preview next occurrence

### 4. Files to create/modify
- Modify `trantrac/models.py` — RecurringTransaction model
- Create migration
- Create management command
- Create templates
- Modify views and urls
- Add cron documentation

## Todo
- [ ] Create RecurringTransaction model and migration
- [ ] Create management command for generation
- [ ] Create CRUD views (HTMX)
- [ ] Create templates
- [ ] Add cron setup docs
- [ ] Add tests
