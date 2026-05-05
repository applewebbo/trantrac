---
# trantrac-8tgh
title: 'Move migrate/collectstatic/tailwind to Coolify pre-deploy for #89'
status: completed
type: task
priority: normal
created_at: 2026-05-05T11:57:50Z
updated_at: 2026-05-05T11:58:04Z
---

Simplify entrypoint.sh to only start granian. Move migrate, tailwind build and collectstatic to Coolify pre-deploy step.

## Summary of Changes

- entrypoint.sh now only starts granian
- migrate, tailwind build and collectstatic moved to Coolify pre-deploy step:
  python manage.py migrate && python manage.py tailwind build && python manage.py collectstatic --no-input
