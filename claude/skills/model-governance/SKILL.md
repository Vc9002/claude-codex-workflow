---
name: model-governance
description: "Champion/challenger governance for model work: promotion-request preflight (own evidence vs gate, producer-to-consumer trace), fail-closed production routing integrity, artifact_hash verification, and incumbent-reproduction gates for ablations. Use when promoting/activating a model, editing registries or routing, auditing artifacts, or building an ablation/benchmark harness."
---

# model-governance

Consolidated from: promotion-request-preflight, production-routing-integrity, artifact-hash-verification, ablation-reproduction-gate. Each section below is the original skill, unchanged apart from heading level.

---

<!-- from skill: promotion-request-preflight -->
## Promotion Request Preflight

**Created by Vincent Chen**

"Promote X" is an instruction about intent, not a verified statement that
X is promotable — and not evidence that anything is wired to consume the
promotion.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

### When to use

Acting on any short directive to promote, activate, or roll out a model,
feature, or config — especially where the directive comes without
attached evidence.

### The rule — two-part preflight, report before executing

1. **Evidence check.** Read the candidate's OWN recorded evaluation and
   any eligibility/qualification block (its artifact, not your memory of
   it), and compare against the project's documented gate. A candidate can
   be promoted with its own artifact recording a failed holdout (CI
   entirely negative) and an explicit `eligible: false` — shipping it
   would activate a known underperformer.
2. **Wiring check.** Trace the producer-to-consumer path: confirm a live
   consumer actually reads what the promotion mutates. If the promotion
   command mutates a map that no serving path reads for the target market,
   the promotion "succeeds" and produces exactly zero predictions — a
   config change nothing consumes is indistinguishable from success until
   someone looks for the output.

Surface a conflict as a blocker with the specific numbers (CI bounds,
gate value, which consumer reads what), rather than executing or silently
declining. The directive is then either rescinded or amended with the
facts on the table.

### Pre-flight check

Before executing a promotion: the artifact's own evaluation was read and
compared against the documented gate, the consumer chain was traced end to
end and confirmed to read the mutated entry, and any conflict was surfaced
as a numbered blocker.

**Principle:** a promotion directive encodes intent, not eligibility and
not wiring; check the candidate's own recorded evidence against the gate,
and confirm the switch you are about to flip is actually read by something
downstream.

---

<!-- from skill: production-routing-integrity -->
## Production Routing Integrity

**Created by Vincent Chen**

An open-source discipline for production model registries and live serving routes: validate
that active workflows match declared serving contracts, eliminate silent drift
across compatibility mirrors, and fail closed when routes or artifacts disagree.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

### When to use

Modifying, auditing, or designing production model registries, serving entry points,
compatibility mirrors (legacy allowlists, artifact maps, champion-challenger routers),
or system health checks in automated ML/inference pipelines.

### Rule 1 — a registry is not valid merely because registered entries pass

A registry health check that evaluates only registered entries can report
100% green while daily scheduled workflows continue to execute unregistered or
legacy models. A valid registry must account for every active producer and consumer
in the codebase.

**Before declaring registry health green:**
1. Enumerate all active scheduled jobs, live CLIs, and serving entry points.
2. Verify that every model executed by an active workflow resolves to a declared,
   validated entry in the authoritative model registry.
3. If an active workflow executes a non-serving or deprecated model by design,
   it must be explicitly flagged as a degraded/transitional state, never silently
   omitted.

### Rule 2 — reconcile compatibility mirrors against one authoritative model list

When legacy allowlists, artifact maps, dashboard status tables, and routing
dictionaries coexist, they inevitably drift if maintained independently.

**To prevent registry split-brain:**
1. Designate a single authoritative model definition table/list.
2. Derive all backward-compatibility mirrors dynamically or validate them via
   hard contract assertions in CI/test suites.
3. Assert bi-directional parity: every model in the compatibility mirror exists
   in the authoritative registry, and every active registry entry is accounted for.

### Rule 3 — enforce exact model-to-artifact identity and fail closed

Live prediction paths must never execute hardcoded heuristics or uncalibrated
defaults under the version string of a trained, validated artifact.

**Before serving inference:**
1. Enforce exact artifact SHA-256 hash matching at load time.
2. Route production serving exclusively through the verified champion artifact
   for each domain/market.
3. Fail closed immediately if an artifact is missing, hash-mismatched, or if the
   live feature calculation differs from the batch training ledger.

### Rule 4 — isolate optional ledger mirrors without weakening required writes

Classify each write by its actual contract before changing exception handling:
primary durable records, required audit/integrity/execution records, or optional
reporting mirrors. A secondary destination is not automatically optional.

1. Commit the primary durable record before attempting an optional mirror, or
   prove that the primary commit independently survives mirror failure. Preserve
   candidate processing when an optional mirror rejects an unsupported domain.
2. Catch expected mirror failures at the optional writer boundary. Emit explicit
   diagnostics with record identity and a degraded mirror status; do not silently
   swallow exceptions or report complete synchronization.
3. Required integrity, audit, and execution writes remain fail closed: failure
   blocks the action or success claim they gate. Optional-mirror handling must
   never wrap the whole transaction or downgrade a required failure.
4. Retry optional mirrors by stable record identity with idempotent writes so a
   retry cannot duplicate primary records or execution. Report unresolved lag.

Before repairing existing ledger/config state, make and verify a backup, parse
serialized fields before merging, and verify preservation of unrelated data.

**Semantic checks:** inject an optional mirror configuration failure and verify
the primary record persists and subsequent candidates are recorded; verify a
required audit failure blocks the gated action; retry a mirror write and verify
one logical record and no repeated execution. Check material child exits in any
supervisor gate; an optional mirror may be degraded, but required stages must all
succeed.

### Pre-flight check

Before shipping changes to model registries or serving routes:
1. Verify all active scheduled jobs map to registered, qualified models.
2. Confirm compatibility mirrors are validated against the authoritative registry.
3. Assert that live forecast paths fail closed on missing/invalid artifacts.
4. Verify that non-serving active pipelines surface as explicit degraded states.
5. Verify optional mirror failures preserve primary durable records and surface
   degraded status; required write failures still block their gated actions.
6. Verify idempotent mirror retries and compare evaluated workflow counts with
   the actual active population before making completeness claims.

---

<!-- from skill: artifact-hash-verification -->
## Artifact Hash Verification (internal)

Verifies embedded `artifact_hash` fields in `config/models/` JSON model
artifacts. Internal skill: contains this repo's specific conventions.

### The convention grid

Recompute the hash as sha256 of `json.dumps(payload_without_artifact_hash,
sort_keys=True)` over a 2×2 grid of serializers before declaring a
MISMATCH: separators `(",", ":")` (compact) vs default `(", ", ": ")`,
each with `ensure_ascii=False` vs `True`. Then try `sort_keys=False` and
raw-text variants.

- Production and archived artifacts (regression models, esports v3–v6,
  measured-edge, kbo/npb, market-residual, ablation) verify with
  **compact separators + ensure_ascii=False**.
- The 2026-08-11 challenger rebuilds (nfl/wnba/tennis rebuild) verify with
  **default separators + ensure_ascii=True** — a compact-only checker
  reports false MISMATCHes on these.
- Calibrator files carry `calibrator_hash`/`base_model_hash` instead of
  `artifact_hash` — no recomputation standard applies to them.

### Expected non-verifiers

- `archive/wnba-spread-baseline-v1.json` — `_retired` fields were appended
  after hashing; expected, not corruption.
- `challengers/mlb-two-head-v1.json`, `mlb-two-head-real-features-v1.json`,
  `soccer-poisson-dc-rebuild-v1.json` — stale hashes (content edited
  post-generation); treat as findings to re-hash, not proof of tampering,
  until git history shows otherwise.

### Pre-flight

Before reporting any hash result:

- Run the full grid — a MISMATCH under one convention is not a mismatch.
- For a genuine non-verifier, check git history for post-generation edits
  before calling it corruption.
</content>

---

<!-- from skill: ablation-reproduction-gate -->
## Ablation Reproduction Gate

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

### When to use

Building, modifying, or re-running any harness that measures multiple
candidate configurations (features, model variants, code paths) against an
incumbent/shipped baseline, where the incumbent's own numbers are already
known from production or a prior documented run.

### The rule

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

### Anti-pattern

Reporting a full table of challenger-vs-baseline deltas with the
incumbent-reproduction question addressed only informally ("looks about
right") or not at all. A large, precise-looking table of numbers reads as
authoritative regardless of whether the pipeline underneath was ever
validated against known truth — the gate is what earns that authority.

### Pre-flight check

Before reporting any ablation/benchmark result, confirm: the incumbent's
own configuration was run as a control variant inside this harness, its
output was compared against the incumbent's previously-shipped numbers, and
either reproduction succeeded (report the match explicitly) or the report
leads with the reproduction failure, not with candidate rankings.

### Rule 4 — measure parity per row, not just in aggregate

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

### Rule 5 — a verdict must consume the uncertainty interval it computes, not the point estimate

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

### Pre-flight check addendum

Also confirm: (4) the report includes a per-row parity table (stored vs.
reproduced, per-feature deltas, mismatch class), not just aggregate bands;
(5) any verdict derived from a computed interval actually gates on that
interval's bound plus a minimum-effect threshold, not the bare point
estimate.
