---
# trantrac-rg3c
title: 'Feature: Telegram alerts for large transactions'
status: todo
type: feature
priority: low
created_at: 2026-02-11T20:48:46Z
updated_at: 2026-02-11T20:48:46Z
---

## Plan

### 1. Alert threshold configuration
- Add `alert_threshold` field to User model (or a new UserPreferences model)
- Default: 100 EUR
- Configurable per user via settings page or Telegram command

### 2. Alert trigger
- In transaction_service.py, after saving a transaction:
  - Check if amount > user threshold
  - If yes, send Telegram notification with details
- Message format: "⚠️ Spesa elevata: €{amount} - {description} ({category})"

### 3. Telegram command
- Add /soglia command to set alert threshold
- `/soglia 200` → sets threshold to 200 EUR
- `/soglia` → shows current threshold

### 4. Files to modify
- Modify User model or create UserPreferences
- Modify `telegram_bot/services/transaction_service.py`
- Add handler for /soglia command
- Create migration

## Todo
- [ ] Add alert threshold to user preferences
- [ ] Implement alert check after transaction save
- [ ] Add /soglia Telegram command
- [ ] Add tests
