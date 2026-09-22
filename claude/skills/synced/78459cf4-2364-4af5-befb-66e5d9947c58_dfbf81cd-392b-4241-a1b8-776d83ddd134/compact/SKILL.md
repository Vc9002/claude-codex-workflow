---
name: compact
description: >
  Session summarizer for copy-paste handoff between sessions. Trigger immediately when the user types "/compact" or "compact" or asks to "summarize the session," "write a handoff," "save context," or "pick up where we left off." Produces a dense plain-text summary in the chat for the user to copy and paste.
---

# Compact

When the user runs `/compact`, output a plain-text session summary directly in the chat. No files. No handoff.md. Just dense, specific prose the user can copy and paste into the next session to restore full context.

## What to cover

Write one continuous block of text (no headers, no bullets) that covers:

- What was built or changed, with exact file paths
- Every key decision made and the reasoning behind it
- What was rejected and why
- Precise numbers (exact, not rounded)
- Any conditional logic or open branches (IF X then Y, BUT IF Z)
- Open questions that were raised but not resolved
- The exact last action taken and its outcome
- What should happen next

End with: "Next session should start by: [exact next step]."

## Rules

- No bullet points. No headers. No padding. Prose only.
- Be dense and specific. Names, paths, numbers — don't generalize.
- If a decision was debated, include what was rejected and why.
- If a number came from a specific source, say so.

## Example output shape

"We edited Vincent_Chen_Resume_2026-04-13.docx (at /sessions/.../mnt/Recruiting/). Rewrote two WUFC Case Team bullets: bullet 1 now reads 'Build DCF, trading comps, and transaction comps models...' replacing the old 'presenting valuation outputs to club analysts' line; bullet 2 replaced Porter's Five Forces framing with exit market research (mapping acquirers, benchmarking exit multiples, framing return scenarios). Validation passed, 46 paragraphs unchanged. PDF version not regenerated and may be stale. Next session should start by: regenerating the PDF if needed for applications."
