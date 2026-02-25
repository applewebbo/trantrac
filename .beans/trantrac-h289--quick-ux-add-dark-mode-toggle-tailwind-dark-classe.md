---
# trantrac-h289
title: 'Quick UX: Add dark mode toggle (Tailwind dark classes + user preference)'
status: completed
type: task
priority: normal
created_at: 2026-02-24T07:08:28Z
updated_at: 2026-02-25T07:52:54Z
parent: trantrac-iv16
---

## Target Release\n\n2026.6\n\n## Acceptance Criteria\n\n- [ ] Anti-flash script in head sets data-theme from localStorage\n- [ ] Toggle button visible in navbar (desktop + mobile)\n- [ ] Clicking toggles between emerald (light) and business (dark)\n- [ ] Preference persisted in localStorage\n- [ ] Sun/moon icons switch correctly\n- [ ] System preference used as default if no localStorage value\n- [ ] Tests verify button and script presence\n\n## Issue\n\n#69

## Summary of Changes\n\nAdded anti-flash script in head that reads from localStorage. Toggle button (moon/sun SVG) added to navbar, always visible. toggleTheme() function switches between emerald/business themes and persists to localStorage. DOMContentLoaded syncs icon state on page load.
