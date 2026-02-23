---
# trantrac-4wny
title: Add duplicate detection for CSV import using Codice identificativo
status: todo
type: bug
priority: critical
created_at: 2026-02-22T20:00:48Z
updated_at: 2026-02-22T20:00:48Z
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

- [ ] Implement `get_existing_transaction_ids()` using batchGet
- [ ] Skip duplicate rows in `import_csv_to_sheet()`
- [ ] Track and include skipped count in return message
- [ ] Handle empty/missing Codice identificativo
- [ ] Add tests for duplicate detection
- [ ] Add test for empty ID edge case

## Expected Return Message

"Importate 15 transazioni, 3 duplicate saltate"
