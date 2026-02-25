---
# trantrac-0kpl
title: 'Voice Input: Setup self-hosted Whisper service (faster-whisper + Docker)'
status: todo
type: task
created_at: 2026-02-25T07:03:38Z
updated_at: 2026-02-25T07:03:38Z
parent: trantrac-iv16
---

## Target Release\n\n2026.6\n\n## Description\n\nDeploy a self-hosted speech-to-text service using faster-whisper (optimized Whisper implementation). The service will expose a simple HTTP endpoint that accepts audio files and returns transcriptions.\n\n## Acceptance Criteria\n\n- [ ] Add faster-whisper Docker service to docker-compose\n- [ ] Create /transcribe endpoint accepting audio (WAV/WebM) returning JSON {text: str}\n- [ ] Configure service URL via environment variable WHISPER_SERVICE_URL\n- [ ] Service handles Italian language (language=it)\n- [ ] Add WHISPER_SERVICE_URL to env.example\n- [ ] Basic health check endpoint\n\n## Notes\n\nUse small or base Whisper model for speed. The service runs separately from the Django app.
