---
name: ablation-reproduction-gate
description: Any ablation, benchmark, or challenger-vs-incumbent harness needs a built-in incumbent-reproduction gate — run the incumbent's exact configuration as a named control variant, compare against its own previously-shipped/documented numbers, and hard-stop or loudly flag when it can't reproduce. Use when building or re-running any harness that compares candidate variants against a shipped baseline.
---

# Ablation Reproduction Gate

**Created by Vincent Chen**

One rule for benchmark/ablation harnesses: before trusting any
candidate-vs-baseline comparison, prove the harness can reproduce the
baseline's own already-known numbers. If it can't, every delta the harness
reports is pipeline noise, not signal about the candidates.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Building, modifying, or re-running any harness that measures multiple
candidate configurations (features, model variants, code paths) against an
incumbent/shipped baseline, where the incumbent's own numbers are already
known from production or a prior documented run.

## The rule

A benchmark that cannot reproduce its own incumbent is measuring pipeline
differences, not candidate differences. If the harness's own re-derivation
of the baseline doesn't match the baseline's previously-shipped or
documented numbers, every other number the harness produces is suspect —
the gap could be a genuinely different row set, a different threshold
definition, a data-freshness mismatch, or any number of pipeline-level
causes that have nothing to do with which candidate is better.

**Build this into the harness, not into post-run analysis:**

1. **Include the incumbent's exact configuration as a named control
   variant** in the same run as the candidates — not a separately-run,
   separately-trusted number from memory or an old doc.
2. **Print a reproduction check** comparing the harness's own
   control-variant output against the incumbent's previously-shipped,
   documented numbers (call counts, accuracy, whatever the domain's
   headline metric is).
3. **Hard-stop or loudly flag when reproduction fails**, before any
   candidate numbers are reported as meaningful. A quiet warning that's
   easy to scroll past defeats the purpose — this needs to block or
   visibly dominate the output.

Building the check into the harness (rather than a manual step someone
remembers to do) means it survives harness changes and reruns automatically
every time the harness is used, instead of being re-discovered as a gap
each time.

## Anti-pattern

Reporting a full table of challenger-vs-baseline deltas with the
incumbent-reproduction question addressed only informally ("looks about
right") or not at all. A large, precise-looking table of numbers reads as
authoritative regardless of whether the pipeline underneath was ever
validated against known truth — the gate is what earns that authority.

## Pre-flight check

Before reporting any ablation/benchmark result, confirm: the incumbent's
own configuration was run as a control variant inside this harness, its
output was compared against the incumbent's previously-shipped numbers, and
either reproduction succeeded (report the match explicitly) or the report
leads with the reproduction failure, not with candidate rankings.

## Rule 4 — measure parity per row, not just in aggregate

An aggregate reproduction check (call ratio, hit-rate delta, Brier delta —
all "passing") can coexist with meaningful per-row divergence that a
model's smoothing (e.g. a logistic regression) hides in the probability
output. If the harness only reports aggregate bands, it can certify a
reproduction while the actual causes of divergence (specific features
matching in only a fraction of sampled rows, specific factors drifting past
tolerance, unidentifiable rows) stay invisible — exactly the detail needed
to know what would break under a future change.

**Add to the harness:** for every row, emit stored vs. reproduced output,
per-feature deltas, and a mismatch-class label from a fixed taxonomy.
Aggregate bands are the summary of that table, not a substitute for it.
Where the system stores its own per-decision payloads, use them as the
stored side.

## Rule 5 — a verdict must consume the uncertainty interval it computes, not the point estimate

If a harness computes a confidence interval on an improvement metric, its
pass/fail verdict must actually use that interval — not a bare point-estimate
comparison (`improved = candidate < baseline`) computed alongside it. A
verdict that ignores a CI it just calculated can flag a result as "improved"
when the CI straddles zero, or "not improved" when a small gain is
statistically clear but practically negligible in the other direction. Require
the CI's lower bound to exceed zero AND pair it with an explicit
minimum-effect threshold, so statistically-clear-but-trivial gains are
rejected too. If a verdict field and an uncertainty field in the same
artifact can disagree, that disagreement is itself a bug to fix.

**Principle:** Computing an uncertainty measure and then deciding on the
point estimate is worse than never computing it — the artifact looks
rigorous while the decision isn't, and reviewers trust the number that was
ignored.

## Pre-flight check addendum

Also confirm: (4) the report includes a per-row parity table (stored vs.
reproduced, per-feature deltas, mismatch class), not just aggregate bands;
(5) any verdict derived from a computed interval actually gates on that
interval's bound plus a minimum-effect threshold, not the bare point
estimate.
