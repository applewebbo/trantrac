---
# trantrac-0fa5
title: 'Voice Input: Implement Italian speech parser for amount/description extraction'
status: todo
type: task
priority: normal
created_at: 2026-02-24T07:08:15Z
updated_at: 2026-02-25T07:04:24Z
parent: trantrac-iv16
blocked_by:
    - trantrac-imnd
---

## Target Release\n\n2026.6\n\n## Description\n\nParse Italian speech transcription from Whisper into structured transaction fields (amount, description, category hint). Implements a regex-based parser for common Italian speech patterns.\n\n## Acceptance Criteria\n\n- [ ] Parse amount: 'ho pagato 50 euro', 'speso 12,50', 'cinquanta euro'\n- [ ] Parse description: remaining text after amount extraction\n- [ ] Auto-fill form fields: importo, descrizione\n- [ ] Handle edge cases: no amount found, multiple numbers\n- [ ] Unit tests for all parsing patterns\n\n## Notes\n\nKeep it simple: regex-based, no ML. The Whisper service handles speech-to-text; this parses the resulting Italian text.
