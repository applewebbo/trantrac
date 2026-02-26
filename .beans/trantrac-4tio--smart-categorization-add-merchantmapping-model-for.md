---
# trantrac-4tio
title: 'Smart Categorization: Add MerchantMapping model for common Italian merchants'
status: completed
type: task
priority: normal
created_at: 2026-02-24T07:08:28Z
updated_at: 2026-02-26T11:01:48Z
parent: trantrac-iv16
---

## Target Release\n\n2026.6

## Plan\n\n- [x] Add MerchantMapping model with keyword, category FK, subcategory FK fields\n- [x] Register in admin\n- [x] Create management command populate_merchant_mappings with common Italian merchants\n- [x] Create migration

## Summary of Changes\n\nAdded MerchantMapping model with keyword (unique), category FK, subcategory FK. Registered in admin with search and filter. Created management command populate_merchant_mappings with ~45 common Italian merchants. Migration 0009 created.
