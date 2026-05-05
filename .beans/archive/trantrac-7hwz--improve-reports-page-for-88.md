---
# trantrac-7hwz
title: 'Improve reports page for #88'
status: completed
type: feature
priority: normal
created_at: 2026-05-05T08:59:43Z
updated_at: 2026-05-05T09:53:11Z
---

Update creation date on force regeneration, remove download form section, add admin-only force-recreate section with month/year selector

## Summary of Changes

- MonthlyReport.generated_at changed from auto_now_add to default=timezone.now; updated in update_or_create defaults so force-regeneration updates the timestamp
- Removed 'Scarica un report' POST form section from reports_list template
- Added admin-only 'Rigenera report' section with month select + year input
- reports_list view simplified to GET-only with require_GET decorator
- New regenerate_report view (POST, staff-only) with lazy pdf_generator import
- Migration 0011: alter generated_at on MonthlyReport
- bin/codeberg: fix token reading with cut -f2- to handle tokens containing =
