---
id: '0000000001'
slug: voice-input-implement-italian-speech-parser-for-amountdescription-extraction
title: 'Voice Input: Implement Italian speech parser for amount/description extraction'
labels:
  - task
created: '2026-08-10T12:04:49.363+02:00'
updated: '2026-08-10T12:04:49.363+02:00'
---

## Description

## Target Release

2026.7

## Description

Parse Italian speech transcription from Whisper into structured transaction fields (amount, description, category hint). Implements a regex-based parser for common Italian speech patterns.

## Acceptance Criteria

- [ ] Parse amount: 'ho pagato 50 euro', 'speso 12,50', 'cinquanta euro'
- [ ] Parse description: remaining text after amount extraction
- [ ] Auto-fill form fields: importo, descrizione
- [ ] Handle edge cases: no amount found, multiple numbers
- [ ] Unit tests for all parsing patterns

## Notes

Keep it simple: regex-based, no ML. The Whisper service handles speech-to-text; this parses the resulting Italian text.
---

## Task Comments

| Commented At | Comment |
| --- | --- |
