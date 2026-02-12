---
# trantrac-qnlj
title: 'UX: add loading states and HTMX feedback'
status: completed
type: feature
priority: normal
created_at: 2026-02-11T20:48:10Z
updated_at: 2026-02-12T07:15:19Z
---

## Plan

### 1. CSV upload loading indicator
- Add htmx indicator (spinner/progress bar) to CSV upload form
- Show progress feedback during file processing
- Disable submit button while uploading

### 2. HTMX loading states
- Add skeleton/placeholder content for subcategory dropdown during load
- Add htmx-indicator class to all HTMX-triggered elements
- Use DaisyUI loading component

### 3. General feedback
- Add aria-live regions for dynamic content updates
- Ensure messages container has proper ARIA attributes

## Todo
- [ ] Add loading spinner to CSV upload form
- [ ] Add skeleton loader for subcategory dropdown
- [ ] Add htmx-indicator to HTMX elements
- [ ] Add aria-live to dynamic regions
- [ ] Test on mobile devices

## Summary of Changes

- Added hx-indicator (#subcategory-loading) to category Div in forms.py for subcategory load feedback
- Added DaisyUI loading spinner next to subcategory field (htmx-indicator class)
- Added hx-disabled-elt to CSV upload form and transaction form (disables submit during request)
- Added aria-live=polite + aria-atomic to messages container in base.html
- Added aria-live=polite + aria-atomic to #transaction_form in index.html
