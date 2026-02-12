---
# trantrac-j04c
title: 'Feature: statistics dashboard with spending trends'
status: scrapped
type: feature
priority: normal
created_at: 2026-02-11T20:48:22Z
updated_at: 2026-02-12T14:08:46Z
---

## Plan

### 1. Data aggregation (trantrac/stats.py)
- Fetch monthly income/expense totals from Google Sheets
- Calculate month-over-month changes
- Category breakdown per month
- Top spending categories

### 2. Dashboard view (trantrac/views.py)
- New view at /stats/ or /dashboard/
- Show:
  - Monthly income vs expenses bar chart
  - Spending by category (pie/donut chart)
  - Month-over-month trend line
  - Current month summary card

### 3. Frontend
- Use Chart.js or lightweight alternative (no heavy JS frameworks)
- DaisyUI stat cards for summary numbers
- HTMX for period selector (month/quarter/year)
- Responsive layout

### 4. Files to create/modify
- Create `trantrac/stats.py` — data aggregation logic
- Create `templates/trantrac/dashboard.html` — dashboard template
- Modify `trantrac/urls.py` — add route
- Modify `trantrac/views.py` — add view
- Modify `templates/includes/navbar.html` — add nav link
- Add Chart.js to static files

## Todo
- [ ] Create stats.py with data aggregation functions
- [ ] Create dashboard view
- [ ] Create dashboard template with Chart.js
- [ ] Add period selector (HTMX)
- [ ] Add navbar link
- [ ] Add tests for stats functions
- [ ] Add tests for dashboard view

## Reasons for Scrapping

Decision to not implement this feature.
