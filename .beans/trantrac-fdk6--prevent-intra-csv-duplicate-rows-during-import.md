---
# trantrac-fdk6
title: Prevent intra-CSV duplicate rows during import
status: completed
type: bug
priority: high
created_at: 2026-02-24T08:08:13Z
updated_at: 2026-02-24T08:13:30Z
---

The current duplicate detection (get_existing_transaction_ids) only checks against existing Google Sheets data. If the same CSV row appears twice within the same file, both rows are imported.

## Solution

Track Codice identificativo values seen during the current import session and skip intra-file duplicates.

## Tasks

- [x] Track seen IDs in a local set during the row-parsing loop
- [x] Skip rows whose ID is already in the seen set
- [x] Count intra-file duplicates in skipped_count
- [x] Add test for duplicate rows within the same CSV
- [x] Add test for empty ID rows (should never be skipped by this check)

## Summary of Changes

Added `seen_in_file` set tracking during the CSV parsing loop. A row is skipped if its Codice identificativo is in either `existing_ids` (from Sheets) or `seen_in_file` (already processed in this import). 1 new test added.
