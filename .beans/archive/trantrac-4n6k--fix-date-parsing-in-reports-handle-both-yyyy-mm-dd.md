---
# trantrac-4n6k
title: 'Fix date parsing in reports: handle both YYYY-MM-DD and dd/mm/yyyy formats'
status: completed
type: bug
priority: normal
created_at: 2026-02-11T14:21:42Z
updated_at: 2026-02-11T14:26:34Z
---

parse_italian_date only handles dd/mm/yyyy but the web form saves dates as YYYY-MM-DD (views.py:46), causing filter_by_month to find no rows and report all-zero values.

## Summary of Changes
- Fixed parse_italian_date to handle both dd/mm/yyyy and YYYY-MM-DD (ISO) formats
- Fixed parse_italian_amount to strip '€ ' prefix returned by Google Sheets FORMATTED_VALUE API
- Added tests for both fixes (3 new date tests, 3 new amount tests, 3 new filter tests, 1 integration test)
