---
name: audit-reverification-checklist
description: Re-verify audit and review conclusions against live state before reporting them, and treat a "failing" step in a documented audit/test procedure as a hypothesis rather than a finding until its assumptions are checked. Use for any code audit, review, or regression-test verification that takes more than a few minutes, especially on an actively-developed codebase.
---

# Audit Re-verification Checklist

**Created by Vincent Chen**

A short discipline for audits, reviews, and regression-test verification:
treat every claim — your own earlier findings, and any tool/step that
reports "failure" — as provisional until it's re-checked against the
current, real state of the system.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Any audit, code review, or verification pass that takes more than a few
minutes on a codebase other people (or other agent sessions) can also
write to — and any regression test whose "proof it catches the bug" step
(a revert-and-confirm-red convention) needs to be trusted before shipping.

## Rule 1 — re-verify at report time, not at start time

A long audit's conclusions are only as fresh as the snapshot they were
built on. If the audit takes real wall-clock time, the repository can move
under it — another session commits, a scheduled job runs, a file changes.
Re-snapshotting costs seconds; reporting a stale conclusion as current
truth costs trust.

**Do, immediately before writing the final report:**
- Re-check git state: current HEAD, ahead/behind vs. the ref you started
  from, working-tree change count.
- Re-run whatever fast verification commands underpinned your headline
  claims (a specific test file, a quick count query) — not the full suite
  necessarily, but the checks your conclusions actually cite.
- If anything shifted, note what changed and whether it affects the
  conclusion, rather than silently reporting the earlier number.

**Anti-pattern:** treating the first snapshot as authoritative because
"that's when I checked" — on a fast-moving repo, "when I checked" and "now"
can be materially different states, and the report should describe now.

## Rule 2 — a failing audit step is a hypothesis, not a finding

Documented audits often embed specific commands or scripts (a hash-check
snippet, a schema-diff query, a config-consistency check). When one of
these reports a mismatch or failure, that's a claim about the codebase —
not yet a verified defect. Two things routinely make a step lie:

1. **The step's own conventions are stale.** A hash-check snippet written
   against an older serialization convention (a different separator style,
   a different string-escaping default) will flag every current file as
   "corrupted" even though nothing is wrong — the step, not the data, is
   out of date. Check: does the audit step's own logic match what the
   codebase's real loader/writer actually does today?
2. **The flagged object has no real consumers.** A "dangling reference" or
   "orphaned config key" finding is only a finding if something actually
   reads that reference. Grep for consumers before reporting a dead key as
   a live bug.

**Before escalating any audit-step failure:** verify the step's own
assumptions against current code, and verify the flagged artifact is
actually consumed by something. Report both what failed and what you
confirmed about it — "step X reports mismatch; verified the step's
convention matches the current loader and the object has N live
consumers" is a finding; "step X reports mismatch" alone is not.

## Rule 3 — a green regression test proves nothing about the fixture

This generalizes rule 2 to test verification specifically. The standard
"revert the fix, confirm the new test fails, restore the fix, confirm it
passes" convention is only as strong as the fixture is faithful — a
fixture that doesn't route through the *same* code path the real bug used
can pass green under both the buggy and fixed code, proving nothing.

Two concrete failure shapes to check for before trusting a revert-check:

- **The fixture skips the code path that actually exhibited the bug** (e.g.
  a malformed record the parser silently drops before reaching the buggy
  logic at all) — old and new code produce the same output because neither
  ever touches the bug.
- **A test helper "conveniently" sets up valid state**, silently
  re-creating the exact artifact the test was supposed to prove is
  missing/broken, so the assertion never actually exercises the failure
  condition.

**Before trusting a revert-check as proof:** trace the fixture through the
same parser/loader/helper chain the production code uses, and confirm the
"break" step (reverting the fix) actually changes the test's outcome for a
reason that maps to the real bug — not for an unrelated reason.

## Rule 4 — a pasted or externally-authored review is stale until re-verified

When executing a review authored elsewhere — pasted from another session,
another tool, or a teammate — every structural claim it makes (branch
topology, process ownership, function/variable names, file paths) is
unverified by definition, because the reviewer's snapshot of the tree is
unknown. Treat these claims exactly like Rule 2's "failing step": a
hypothesis, not a finding.

**Before acting on a pasted review:** re-check each structural claim
against the live tree — branch ahead/behind state, actual process
ownership (pid/launchd, not assumption), whether cited function/variable
names actually exist in the current source. Acting on unverified claims
risks writing fixes for problems that no longer exist (or never did) while
the review's underlying analysis may still be right once its premises are
corrected.

**Principle:** A review's conclusions are only as fresh as the snapshot
they were built on — and when the reviewer is a different session or tool,
that snapshot is unknown by definition. Verify the structural claims
first; the analysis may still be right even when its premises have moved.

## Rule 5 — a merge/sync claim is a claim, not a fact

Before trusting any "synced with main" / "merged from X" statement — in a
commit message, a doc, or verbally — as grounds for running a gate or
reproduction test whose result will be recorded as authoritative: check the
actual parent chain (`git merge-base --is-ancestor <claimed-sha> HEAD`), not
the message. A merge commit's message can claim a SHA that isn't actually
an ancestor, silently omitting real commits (including bugfixes) from what
looks like a synced branch.

## Rule 6 — pin parity checks to raw projections after authority cutovers

Once an application switches to a new authoritative data store (e.g. SQLite
database becoming authoritative while spreadsheets become downstream exports), a
parity checker that calls the high-level application read API can compare the
authoritative store to itself, falsely reporting that stale or incomplete
projections are clean. Furthermore, a legacy bidirectional reconciliation path
can silently erase canonical records because the projection omitted them.

**Before verifying parity or reconciliation after a storage authority cutover:**
1. Require parity tooling to read the raw projection directly and physically
   independent of the application read API.
2. Explicitly declare the authoritative source and reconciliation direction.
3. Enforce reconciliation direction strictly with tests: canonical-to-projection
   only after cutover, never projection-to-canonical.

## Rule 7 — gates failing on by-construction conditions require loud named exceptions, not silent passes

When a strict sanity, distribution, or collinearity gate legitimately fails on
conditions that are collinear or duplicate by construction or source limitations,
weakening global gate thresholds or silently passing the check destroys the gate's
ability to catch real regressions.

**When a gate fails on a known-by-construction condition:**
1. Do NOT relax the global gate threshold or drop columns ad hoc.
2. Define a dedicated, explicitly named `KNOWN_EXCEPTIONS` list with documented
   per-entry rationale.
3. Emit a prominent, loud `[KNOWN]` output log line for each matched exception.
4. Keep the gate strict and fail-closed for all unlisted conditions.

## Rule 8 — an authoritative source is evidence, not proof, for high-stakes content

Official formula sheets, published answer keys, and other "authoritative"
sources can themselves contain errors — a sign flip in a formula, a
misclassified approximation, a rounded final digit from low-precision
intermediate arithmetic. Treating source authority as sufficient
verification propagates these errors downstream.

**For every high-stakes formula or worked answer sourced from an
authority:** independently differentiate, expand, or numerically evaluate
it rather than transcribing it as-is. When your independent check
conflicts with the source, record it as an explicit source error rather
than silently deferring to authority. Prioritize adversarial checks at the
places errors hide best: sign-sensitive identities, approximation
direction (over- vs. under-estimate), and rounded numerical endpoints.

## Pre-flight check

Before delivering any audit or review report, re-read this checklist
against your own draft and confirm: (1) git/state snapshot was refreshed
at report time, not just at start; (2) every "failing step" claim has a
documented convention-check and consumer-check; (3) every "this test now
catches the bug" claim traces through the real code path, not a shortcut
fixture; (4) if executing a pasted/externally-authored review, every
structural claim (branch state, process ownership, names/paths) was
re-checked against the live tree; (5) any "synced/merged" claim underpinning
a gate result was verified via the actual parent chain, not the commit
message; (6) storage parity checks read independent raw projections and pin
reconciliation direction; (7) by-construction gate failures are handled
via explicit, loud named exception lists rather than threshold weakening;
and (8) high-stakes formulas/answers sourced from an authority were
independently re-derived or numerically checked, not just transcribed.
</content>
