---
# trantrac-1dvd
title: 'Quick UX: Add keyboard shortcuts (n=new, /=search, ?=help)'
status: completed
type: task
priority: normal
created_at: 2026-02-24T07:08:28Z
updated_at: 2026-02-25T07:16:40Z
parent: trantrac-iv16
---

## Target Release\n\n2026.6\n\n## Acceptance Criteria\n\n- [x]  key focuses first input in transaction form\n- [x]  key toggles keyboard help dialog\n- [x]  closes the help dialog\n- [x] Shortcuts are disabled when focus is on input/textarea/select\n- [x] Help dialog lists all available shortcuts\n- [x] Tests verify dialog is rendered in page\n\n## Issue\n\n#68

## Summary of Changes

Added keyboard-help dialog to base.html with shortcuts table and vanilla JS keydown handler. Shortcuts: n focuses transaction form, ? toggles help dialog, Escape closes it. Skipped when focus is on form elements. 5 tests added.
