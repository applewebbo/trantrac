---
# trantrac-imnd
title: 'Voice Input: Add Web Speech API component with Alpine.js (adapt from school_menu)'
status: todo
type: task
priority: normal
created_at: 2026-02-24T07:08:15Z
updated_at: 2026-02-25T07:04:24Z
parent: trantrac-iv16
blocked_by:
    - trantrac-0kpl
---

## Target Release\n\n2026.6\n\n## Description\n\nImplement audio recording in the browser using vanilla JS (MediaRecorder API). Sends the recorded audio blob to the self-hosted Whisper endpoint and fills the transaction form fields with the transcription.\n\n## Acceptance Criteria\n\n- [ ] Vanilla JS component (no Alpine.js dependency)\n- [ ] MediaRecorder API for audio capture (WebM/Opus format)\n- [ ] POST recorded audio to Django view which proxies to Whisper service\n- [ ] Graceful degradation: hide microphone button if browser doesn't support MediaRecorder\n- [ ] Show recording state visually (pulsing indicator)\n- [ ] Handle Whisper service errors gracefully
