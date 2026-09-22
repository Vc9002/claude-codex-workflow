---
name: data-pipeline-guardrail-patterns
description: Any scraper or parser feeding a settlement, grading, or decision pipeline must explicitly model the source's "hasn't happened yet" representation and skip it, and must never fabricate a stable identifier when the source hasn't provided a real one. Use when writing or reviewing any ingestion code whose output drives automated decisions.
---

# Data Pipeline Guardrail Patterns

**Created by Vincent Chen**

Two related rules for scrapers/parsers that feed downstream
settlement/grading/decision logic: model absence explicitly, and never
invent identity.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Writing or reviewing any ingestion/parsing code whose output feeds an
automated downstream decision — settlement, grading, scoring, matching,
or any pipeline where a wrong parsed value becomes a wrong real-world
outcome.

## Rule 1 — "parses successfully" is not "happened"

Sources encode "this hasn't happened yet" in their own way — a placeholder
value, an empty field, a specific marker character, a literal zero. A
parser that treats any syntactically valid value as real data will convert
that absence into a fake fact. The canonical failure shape: a
not-yet-completed event is rendered as `0` in a numeric field that would
otherwise hold a real result; a parser with no special-case for "not yet"
happily parses the `0` as a genuine value and the pipeline commits it as
truth.

**Before trusting any parsed field that feeds a decision:** identify how
the source represents "this hasn't happened / isn't available yet" —
explicitly, as its own case — and make the parser skip or defer those rows
rather than parsing them as real data. A sibling source or an earlier
version of the same parser having already solved this (skipping rows
carrying the source's own "pending" marker) is a strong signal of what the
correct behavior looks like — check whether one already exists nearby
before writing the check from scratch.

## Rule 2 — never fabricate a stable identifier

When a source hasn't yet provided a real, stable identifier for a record
(an event ID, a game ID), don't synthesize one to make the row fit a
schema that expects an ID. A fabricated identifier can never merge with the
real identifier once the source provides it — the fabricated row and the
real row become two permanently separate entities referring to the same
underlying thing. If a matcher then has to pick between them (e.g. by sort
order), the fabricated row can win, silently shadowing the real data
forever.

**Prefer a matcher that favors rows carrying real source-provided data**
over rows that merely parsed without error — a fabricated-identifier
pattern is detectable and should lose any tiebreak against a row with a
genuine source ID.

## Worked example (abstracted)

A results scraper for one data source rendered not-yet-played events as
`0 vs 0` with no detail link. The parser had no special case for this,
parsed the zeros as real final scores, and fabricated a fallback row
identifier because the source's real ID field was also empty at that
point. Every unplayed event was cached as a genuine tied result. Later,
when the real result and real ID became available, the fabricated-ID row
sorted ahead of it in the matcher and shadowed it — every downstream
decision graded against the fake tie. A parallel parser for a different
source in the same system was immune because it explicitly skipped rows
carrying that source's "unplayed" marker. The fix mirrored that: skip rows
with no real source ID, and make the matcher discount the
fabricated-ID pattern.

## Rule 3 — entry-point tests must pin every side-effect path

A test that drives a real entry point (`main()`, `serve()`, a CLI's main)
end-to-end mutates whatever shared operational files that entry point
touches — pidfiles, lockfiles, state files, log destinations. If the test
doesn't redirect those to tmp paths, it can silently destroy another
subsystem's live evidence (e.g. deleting the real running service's
pidfile) while passing green — the worst failure mode, because it erases
the very thing that would have caught the problem.

**Before trusting any test that calls a real entry point:** confirm every
side-effect path it touches is monkeypatched to a tmp location as part of
test setup, not left to whatever the entry point resolves by default.

## Rule 4 — prospective-capture pipelines need three extra disciplines

For any pipeline capturing data prospectively (before an event resolves) —
where a missed window is a permanently lost row, unlike a pipeline that can
re-derive history:

1. **Model the scheduler's missed-fire semantics explicitly.** A scheduler
   that coalesces missed firings into one post-wake run creates *systematic*
   (not uniform) missingness, concentrated on whichever class of events was
   in-window when it slept through — e.g. late-starting events. Verify
   against that specific class, not just "did a run happen."
2. **Record coverage denominators at capture time.** "How many events were
   still capturable when we looked" is only recoverable if recorded then —
   upstream schedules are often mutable and can't be reconstructed later.
3. **Prove "nothing to do" with pinned deterministic tests.** An empty
   result is indistinguishable from broken logic unless a test asserts it
   deliberately; treat a first-run zero-coverage report in one stratum as
   the bias the system exists to catch, not as a bug to explain away. (A
   related trap: a dedupe key that includes the observation timestamp
   guarantees every run writes "new" duplicates, since the timestamp always
   differs — don't key dedup on a value that's unique by construction.)

**Principle:** The dangerous property of prospective data is that losses are
silent, permanent, and non-uniform — bias enters through the interaction of
the scheduler with the thing being observed, so capture quality must be
measured stratified by whatever variable governs that interaction.

## Rule 5 — settlement payoff dimensionality must match the graded market

Transport integrity, schema validity, and arithmetic checks cannot establish
semantic correctness if the settlement data lacks the dimensions of the market
being graded. Canonical failure shape: a settlement workflow consumes a binary
match-winner result as if it were a score, grading moneyline correctly while
spread and total markets produce mechanically corrupted payoffs despite all
database constraints and hash chains passing.

**Before trusting settlement tests or live grading pipelines:**
1. Enumerate each market's required payoff inputs (e.g. binary winner vs.
   exact point totals vs. inning-by-inning runs).
2. Prove the settlement source supplies those exact dimensions.
3. Test at least one derivative/non-moneyline fixture end-to-end against real
   market contracts before certifying green status.

## Rule 6 — assert domain semantic postconditions before green

A successful pipeline exit code and nominal database writes cannot certify
economically coherent results. Process success is insufficient if the output
violates fundamental domain invariants.

**For any financial or betting ledger pipeline, enforce domain invariants in health checks:**
- Every settled row must have a positive, immutable scoring basis (staked units > 0).
- Wins must yield strictly positive payoff ($P\&L > 0$).
- Loss $P\&L$ must equal negative staked units within numerical precision ($- \text{units} \pm \epsilon$).
- Aggregate all material child exit codes in supervisors — do not allow a partial crash in an intermediate model/pricing stage to be reported as green.

## Pre-flight check

Before shipping or reviewing ingestion code that feeds a decision
pipeline: confirm the source's "not yet happened" representation is
explicitly identified and skipped (not merely parsed); confirm no code
path synthesizes a stand-in identifier for a record the source hasn't
assigned a real one to yet; confirm any test driving a real entry point
pins every side-effect path to tmp; for prospective-capture systems,
confirm missed-fire semantics, capture-time denominators, and "nothing to
do" states are each explicitly handled and tested; confirm settlement data
has the exact dimensionality of the graded markets with derivative fixtures
tested; and verify domain economic invariants (positive basis, win/loss P&L
bounds) are asserted in postconditions.
