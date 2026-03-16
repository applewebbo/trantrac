---
# trantrac-ue6i
title: Migrate app to Coolify
status: completed
type: task
priority: normal
created_at: 2026-03-16T07:59:15Z
updated_at: 2026-03-16T09:05:05Z
---

Migrate trantrac from Caprover to new server with Coolify, configure auto-deploy webhook, update deploy skill

## Tasks\n\n- [x] Creare issue #81 su Codeberg\n- [x] Aggiornare .env.example (rimuovere Caprover, aggiungere Coolify)\n- [x] Aggiornare SKILLS.md con descrizione deploy Coolify\n- [ ] Aggiungere COOLIFY_WEBHOOK_URL e COOLIFY_WEBHOOK_TOKEN al .env reale\n- [ ] Eseguire il primo deploy su Coolify\n- [ ] Verificare app funzionante sul nuovo server

## Summary of Changes\n\n- Migrated production deployment da Caprover a Coolify\n- Aggiornato .env.example con variabili Coolify\n- Aggiornato /deploy skill per webhook Coolify\n- Aggiunto PREPEND_WWW come env var configurabile\n- Aggiornate tutte le dipendenze Python\n- Configurato auto-deploy su push a main via webhook Codeberg → Coolify
