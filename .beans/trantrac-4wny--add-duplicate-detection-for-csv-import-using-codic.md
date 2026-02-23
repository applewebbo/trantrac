---
# trantrac-4wny
title: Add duplicate detection for CSV import using Codice identificativo
status: completed
type: bug
priority: critical
created_at: 2026-02-22T20:00:48Z
updated_at: 2026-02-23T19:29:07Z
parent: trantrac-zm6a
---

## Problem

CSV import does not check for duplicate transactions based on 'Codice identificativo', allowing the same transaction to be imported multiple times.

## Location

`trantrac/utils.py` - `import_csv_to_sheet()`

## Current Behavior

- Reads 'Codice identificativo' from CSV row
- Appends value to sheet row data
- **No duplicate check against existing sheet data**
- Same transaction can be imported multiple times

## Solution

Before processing rows, fetch existing IDs from both sheets and skip duplicates:

```python
def get_existing_transaction_ids() -> set[str]:
    service = get_sheets_service()
    spreadsheet_id = get_spreadsheet_id()
    try:
        result = service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=['ENTRATE!F:F', 'USCITE!H:H']
        ).execute()
        ids = set()
        for value_range in result.get('valueRanges', []):
            for row in value_range.get('values', []):
                if row and row[0]:
                    ids.add(row[0])
        return ids
    finally:
        service.close()
```

## Tasks

- [x] Implement `get_existing_transaction_ids()` using batchGet
- [x] Skip duplicate rows in `import_csv_to_sheet()`
- [x] Track and include skipped count in return message
- [x] Handle empty/missing Codice identificativo
- [x] Add tests for duplicate detection
- [x] Add test for empty ID edge case

## Expected Return Message

"Importate 15 transazioni, 3 duplicate saltate"

## Summary of Changes

Added `get_existing_transaction_ids()` that fetches existing IDs from ENTRATE (col F) and USCITE (col H) via batchGet. Updated `import_csv_to_sheet()` to skip duplicates and return counts in message (e.g. "Importate 5 transazioni, 2 duplicate saltate"). Added 5 new tests with 100% coverage.
