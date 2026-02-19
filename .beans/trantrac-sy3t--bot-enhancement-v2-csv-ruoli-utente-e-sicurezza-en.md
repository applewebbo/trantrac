---
# trantrac-sy3t
title: 'Bot Enhancement v2: CSV, ruoli utente e sicurezza enrollment'
status: completed
type: epic
priority: normal
created_at: 2026-02-19T14:02:35Z
updated_at: 2026-02-19T14:29:08Z
---

## Obiettivo

Potenziare il bot Telegram con tre aree principali:
1. **CSV upload via bot** (solo admin)
2. **Due livelli utente**: admin (is_staff) e utente normale
3. **Enrollment sicuro**: approvazione admin prima di poter usare il bot

## Scope

- Upload CSV da Telegram usando il formato già esistente (stesso dell'upload web)
- Admin = chi ha `is_staff=True` nel Django admin
- Enrollment flow: telefono + email → pending → admin approva/rifiuta via bottoni inline
- Staff users si auto-approvano durante l'enrollment
