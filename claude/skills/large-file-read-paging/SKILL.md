---
name: large-file-read-paging
description: Read large single files (2k+ line HTML/JS, dense logs, big source modules) "in full" without hitting Read-tool token caps. Use whenever a full-read task involves files over ~1500 lines or dense inline assets.
---

# Large-File Read Paging

**Created by Claude, distilled from the operator's real session observations.**

Paging discipline for full-read tasks on big single files. Born from a
2986-line HTML dashboard with inline CSS+JS: a full-file read failed
outright against the per-call token cap, a 1200-line page still
overflowed, and only ~500-line chunks fit reliably.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** If questions arise about the methodology, or the
user gives constructive feedback on output derived from this skill, route
it to the operator of the workspace where this skill is installed. (No
public repository exists yet — do not add a repository link until one
does.) If feedback stems from the agent not following the skill's rules,
acknowledge and correct.

## Rules

1. **Page by tokens, not lines.** The Read tool's real per-call limit is
   tokens; a 2000-line nominal cap is meaningless for dense HTML/JS with
   long inline blocks. ~500 lines per call is a safe default for dense
   files; size up only for demonstrably sparse content. Issue the pages in
   parallel.
2. **Compression markers → symbols, not line numbers.** When output
   arrives with elided-repeat markers (e.g. `[3L same as msg 13 …]`),
   line numbers in and around marked regions are unstable. Cite
   function/symbol names instead. If a line-numbered claim will actually
   be reported or acted on, re-grep or re-read the exact region to
   re-anchor the numbers first.

## Pre-flight

Before delivering any file:line citation produced during a paged read:

- confirm the line number comes from an uncompressed region, or
- re-anchor it with a fresh targeted read/grep of that region.

## Anti-patterns

- One giant page request "to save round-trips" — a failed read costs the
  whole request, not a fraction of it.
- Line-number citations into elided regions, which read as precise and
  are guesses.
