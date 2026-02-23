---
# trantrac-7u55
title: 'Fix failing tests: wrong mock paths'
status: completed
type: bug
priority: normal
created_at: 2026-02-23T14:25:52Z
updated_at: 2026-02-23T14:29:13Z
---

Tests are failing because they mock wrong module paths. Fix:\n1. test_models.py: patch 'trantrac.models.get_sheets_service' → 'trantrac.utils.get_sheets_service'\n2. test_utils.py: patch 'trantrac.utils.save_category_and_sub_to_sheet' → 'trantrac.models.save_category_and_sub_to_sheet'

## Summary of Changes\n\n- Fixed 4 mock paths in test_models.py:  → \n- Fixed 1 mock path in test_utils.py:  → \n- Updated  to raise from  (pre-try call) to cover lines 73-74\n- All 375 tests pass, coverage 100%
