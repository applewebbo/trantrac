---
# trantrac-1z67
title: 'Implement Telegram Bot core functionality for #35'
status: completed
type: task
priority: normal
created_at: 2026-02-05T06:39:12Z
updated_at: 2026-02-05T06:44:08Z
---

Implementa i componenti core del Telegram Bot: Services (parser, suggestions), Handlers (auth, transaction), Views (webhook), URLs, e Management commands.

## Checklist
- [x] Implementa services/parser.py
- [x] Implementa services/suggestions.py
- [x] Implementa services/transaction_service.py
- [x] Implementa handlers/auth.py
- [x] Implementa handlers/transaction.py
- [x] Implementa views.py (webhook)
- [x] Crea urls.py
- [x] Include telegram_bot.urls in core/urls.py
- [x] Implementa management/commands/runbot.py
- [x] Implementa management/commands/setwebhook.py
- [x] Implementa management/commands/retry_pending_transactions.py
- [x] Implementa management/commands/cleanup_auth_sessions.py
