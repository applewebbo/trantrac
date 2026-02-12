---
# trantrac-cy22
title: 'Fix ResourceWarning: close Google Sheets API connections for #38'
status: completed
type: bug
priority: normal
created_at: 2026-02-06T15:35:14Z
updated_at: 2026-02-06T15:40:10Z
---

Fix ResourceWarning about unclosed SSL sockets in Google Sheets API calls.

## Problem:
The `googleapiclient.discovery.build()` service is not being closed properly, leaving SSL connections open.

## Solution:
Modify `trantrac/utils.py` to properly close Google Sheets API service connections:
- Add explicit `.close()` calls after using the service
- Or implement context manager pattern
- Ensure all functions (`save_to_sheet`, `get_sheet_data`, `import_csv_to_sheet`) clean up connections

## Files to modify:
- `trantrac/utils.py`

## Testing:
- Run tests and verify ResourceWarning is gone
- Ensure Google Sheets operations still work correctly
