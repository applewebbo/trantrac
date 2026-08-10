---
id: '0000000006'
slug: voice-input-add-web-speech-api-component-with-alpinejs-adapt-from-schoolmenu
title: >-
  Voice Input: Add Web Speech API component with Alpine.js (adapt from
  school_menu)
labels:
  - task
created: '2026-08-10T12:04:49.540+02:00'
updated: '2026-08-10T12:04:49.540+02:00'
---

## Description

## Target Release

2026.7

## Description

Implement audio recording in the browser using vanilla JS (MediaRecorder API). Sends the recorded audio blob to the self-hosted Whisper endpoint and fills the transaction form fields with the transcription.

## Acceptance Criteria

- [ ] Vanilla JS component (no Alpine.js dependency)
- [ ] MediaRecorder API for audio capture (WebM/Opus format)
- [ ] POST recorded audio to Django view which proxies to Whisper service
- [ ] Graceful degradation: hide microphone button if browser doesn't support MediaRecorder
- [ ] Show recording state visually (pulsing indicator)
- [ ] Handle Whisper service errors gracefully
---

## Task Comments

| Commented At | Comment |
| --- | --- |
