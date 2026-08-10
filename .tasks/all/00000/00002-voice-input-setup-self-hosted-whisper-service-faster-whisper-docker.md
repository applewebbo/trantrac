---
id: '0000000002'
slug: voice-input-setup-self-hosted-whisper-service-faster-whisper-docker
title: 'Voice Input: Setup self-hosted Whisper service (faster-whisper + Docker)'
labels:
  - task
created: '2026-08-10T12:04:49.398+02:00'
updated: '2026-08-10T12:04:49.398+02:00'
---

## Description

## Target Release

2026.7

## Description

Deploy a self-hosted speech-to-text service using faster-whisper (optimized Whisper implementation). The service will expose a simple HTTP endpoint that accepts audio files and returns transcriptions.

## Acceptance Criteria

- [ ] Add faster-whisper Docker service to docker-compose
- [ ] Create /transcribe endpoint accepting audio (WAV/WebM) returning JSON {text: str}
- [ ] Configure service URL via environment variable WHISPER_SERVICE_URL
- [ ] Service handles Italian language (language=it)
- [ ] Add WHISPER_SERVICE_URL to env.example
- [ ] Basic health check endpoint

## Notes

Use small or base Whisper model for speed. The service runs separately from the Django app.
---

## Task Comments

| Commented At | Comment |
| --- | --- |
