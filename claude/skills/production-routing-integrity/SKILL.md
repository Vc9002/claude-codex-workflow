---
name: production-routing-integrity
description: Enforce fail-closed production model routing, eliminate compatibility mirror drift, require exact model-to-artifact identity, and make unrouted active workflows explicit degraded health states. Use when auditing or modifying model registries, serving pipelines, routing contracts, or production health checks.
---

# Production Routing Integrity

**Created by Vincent Chen**

An open-source discipline for production model registries and live serving routes: validate
that active workflows match declared serving contracts, eliminate silent drift
across compatibility mirrors, and fail closed when routes or artifacts disagree.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Modifying, auditing, or designing production model registries, serving entry points,
compatibility mirrors (legacy allowlists, artifact maps, champion-challenger routers),
or system health checks in automated ML/inference pipelines.

## Rule 1 — a registry is not valid merely because registered entries pass

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

## Rule 2 — reconcile compatibility mirrors against one authoritative model list

When legacy allowlists, artifact maps, dashboard status tables, and routing
dictionaries coexist, they inevitably drift if maintained independently.

**To prevent registry split-brain:**
1. Designate a single authoritative model definition table/list.
2. Derive all backward-compatibility mirrors dynamically or validate them via
   hard contract assertions in CI/test suites.
3. Assert bi-directional parity: every model in the compatibility mirror exists
   in the authoritative registry, and every active registry entry is accounted for.

## Rule 3 — enforce exact model-to-artifact identity and fail closed

Live prediction paths must never execute hardcoded heuristics or uncalibrated
defaults under the version string of a trained, validated artifact.

**Before serving inference:**
1. Enforce exact artifact SHA-256 hash matching at load time.
2. Route production serving exclusively through the verified champion artifact
   for each domain/market.
3. Fail closed immediately if an artifact is missing, hash-mismatched, or if the
   live feature calculation differs from the batch training ledger.

## Rule 4 — isolate optional ledger mirrors without weakening required writes

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

## Pre-flight check

Before shipping changes to model registries or serving routes:
1. Verify all active scheduled jobs map to registered, qualified models.
2. Confirm compatibility mirrors are validated against the authoritative registry.
3. Assert that live forecast paths fail closed on missing/invalid artifacts.
4. Verify that non-serving active pipelines surface as explicit degraded states.
5. Verify optional mirror failures preserve primary durable records and surface
   degraded status; required write failures still block their gated actions.
6. Verify idempotent mirror retries and compare evaluated workflow counts with
   the actual active population before making completeness claims.
