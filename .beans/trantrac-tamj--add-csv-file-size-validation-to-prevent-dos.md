---
# trantrac-tamj
title: Add CSV file size validation to prevent DoS
status: completed
type: bug
priority: critical
created_at: 2026-02-22T19:53:42Z
updated_at: 2026-02-23T18:06:43Z
parent: trantrac-zm6a
---

## Problem

No file size limits on CSV uploads, risking memory exhaustion and DoS attacks.

## Affected Files

- `trantrac/views.py:115-136` (upload_csv view)
- `telegram_bot/handlers/csv_upload.py:26-52` (bot CSV handler)

## Tasks

- [ ] Add MAX_CSV_SIZE constant (10MB recommended)
- [ ] Validate file size before processing in web upload
- [ ] Validate file size before processing in bot upload
- [ ] Return user-friendly error message if file too large
- [ ] Add test cases for oversized files

## Implementation

```python
MAX_CSV_SIZE = 10 * 1024 * 1024  # 10MB

if csv_file.size > MAX_CSV_SIZE:
    messages.error(request, "File troppo grande (max 10MB)")
    return redirect('index')
```
