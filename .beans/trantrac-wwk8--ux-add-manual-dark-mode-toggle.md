---
# trantrac-wwk8
title: 'UX: add manual dark mode toggle'
status: todo
type: feature
priority: low
created_at: 2026-02-11T20:48:14Z
updated_at: 2026-02-11T20:48:14Z
---

## Plan

### 1. Theme toggle component
- Add toggle button in navbar (sun/moon icon)
- Use DaisyUI theme-controller or Alpine.js for toggle
- Persist preference in localStorage

### 2. Implementation
- Add `data-theme` attribute toggle on `<html>` element
- On load: check localStorage, fallback to system preference
- On toggle: update localStorage + DOM

### 3. Files to modify
- `templates/includes/navbar.html` — add toggle button
- `templates/base.html` — add theme init script
- Possibly `static/css/source.css` for DaisyUI theme config

## Todo
- [ ] Add theme toggle button in navbar
- [ ] Implement localStorage persistence
- [ ] Handle system preference fallback
- [ ] Test light/dark transitions
- [ ] Ensure all components look correct in both themes
