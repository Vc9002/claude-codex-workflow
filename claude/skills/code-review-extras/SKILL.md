---
name: code-review-extras
description: Companion to the read-only `code-review` plugin skill (this file carries only the delta). Three additions for parallel-review and removed-behavior passes: cluster finder candidates by (file, line, mechanism) before spending verification budget; when a diff splits validate from persist, answer the four state-boundary questions; and scheduler+observer pairs must share the observed API's locality convention.
---

# Code Review Extras (delta companion to the `code-review` skill)

**Created by Vincent Chen**

Delta guidance layered on top of the `code-review` plugin skill, which is
read-only. Use this file in the same sessions where `code-review` runs.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## 1. Parallel finder reviews: cluster candidates by mechanism before verifying

When N independent finder agents run in a recall-mode review, the same 4–5
mechanisms get independently rediscovered by every finder under
textually different descriptions, while the genuinely distinct second-order
angles come from single finders. Spending one verification pass per finder
report burns the budget on duplicates.

- After the finder phase, add an explicit clustering pass: group candidates
  whose (file, line, mechanism) intersect; keep the sharpest failure
  scenario per cluster; run ONE verifier per cluster.
- The verifier count follows mechanisms, not finder reports.
- Read convergence itself as signal: "N finders converged on the same
  line" is a severity signal; "single finder with a cross-module
  mechanism" is a reachability question to chase.

**Principle:** finding is not the bottleneck in parallel finder reviews;
ranking and deduplication are.

## 2. Removed-behavior checklist: state-boundary questions for a validate/persist split

When a diff splits one function into validate-then-persist (or
preflight/commit, or plan/execute), the old invariant "compute and write in
one lock" becomes a new one: "the state I validated is the state I
persist" — and rollback snapshots must be taken at the same state boundary
as the mutation they undo. Three separate bugs (stale sizing, stale
restore, store divergence) can share this one root cause.

Ask explicitly: (a) which ledger/state each phase READS, (b) which store
each phase WRITES, (c) where the rollback snapshot is taken relative to
destructive steps, (d) whether the snapshot's write path mirrors to every
store the mutations touch.

## 3. Scheduler + observer pairs must share the locality convention

When a scheduler/planner and its observer/collector both consume a
third-party API but compute dates independently (one UTC-today, the other
each event's local date), the scheduler wakes the observer at the wrong
time and the loss is silent and permanent — exactly the class of data that
can't be backfilled. In review, state each script's timezone convention
explicitly, and cross-check the planner's output date against the
observer's date computation for the same event. Treat "nothing to do"
output from a quiet observer as evidence of a convention mismatch, not
success.

**Principle:** the locality convention of the observed system must be a
shared, explicit constant, verified end to end.

## 4. A bug-class fix in one function is a grep target, not a closed ticket

When a fix corrects one instance of a bug class — a falsy-zero default
(`x = payload.get(...) or default`, which silently substitutes the default
for a genuine `0`/`0.0`/`False`), a missing null check, an off-by-one — the
same field-parsing idiom tends to recur in sibling functions in the same
file or module that share the pattern but weren't the one reported broken.
Fixing only the reported call site leaves the sibling live. After any
bug-class fix, grep the file/module for the same pattern (same operator,
same field name, same idiom) before calling the fix complete, not just the
line that was reported.

Separately, for any "re-verify already-settled record" logic (re-grading a
terminal state from external data — scores, exchange resolutions, upstream
statuses): check for terminal-non-outcome sentinel values (void, cancelled,
expired-no-fill) and short-circuit before recomputing a result. A
terminal-but-not-graded state is distinct from open-pending-grading; without
the short-circuit, a deliberate correction (e.g. manually voiding a
zero-fill row) gets silently reverted the next time the re-verification
pass runs.

**Principle:** a bug-class fix at one call site is evidence the class
exists in the codebase, not evidence it's contained — same-pattern grep
across the file/module is part of the fix, not a follow-up.

## Pre-flight check

Before delivering a review: finder candidates were clustered by mechanism
before verification budget was spent; any validate/persist split in the
diff has all four state-boundary questions answered; any scheduler+observer
pair has its timezone convention stated in both scripts and cross-checked;
any bug-class fix in the diff was grepped for the same pattern elsewhere in
the file/module, and any re-verification-of-settled-record logic has a
terminal-non-outcome short-circuit.
