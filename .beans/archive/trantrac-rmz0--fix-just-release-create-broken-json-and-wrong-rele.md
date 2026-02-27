---
# trantrac-rmz0
title: 'Fix just release-create: broken JSON and wrong release name'
status: completed
type: bug
priority: normal
created_at: 2026-02-26T13:53:17Z
updated_at: 2026-02-26T13:55:27Z
---

The release-create recipe embeds BODY directly in a JSON string literal, but FEATURES/FIXES/etc. contain real newlines that produce invalid JSON (URL: null). Fix by using jq -n --arg to safely encode the body. Also remove the 'Release ' prefix from the release name (should be 'v2026.6', not 'Release v2026.6'). Ref: issue #74

## Summary of Changes\n\n- Replaced direct JSON string interpolation with `jq -n --arg body` to safely encode multiline body\n- Fixed release name: removed 'Release ' prefix (now 'v2026.6' instead of 'Release v2026.6')\n- Fixed `\n` literals in BODY by using `NL=$'\n'` variable for real newlines throughout\n- Added `-s` flag to curl for clean output
