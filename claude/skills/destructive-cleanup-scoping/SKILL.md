---
name: destructive-cleanup-scoping
description: Scope any destructive cleanup (deletes, mass-corrections) by the exact identity of the bad data — unique IDs, known-bad values, a verified enumerated list — never by a time window, which can silently catch legitimate concurrent writes. Use before running any delete/correction against live data.
---

# Destructive Cleanup Scoping

**Created by Vincent Chen**

One rule for authorized data cleanup: scope by identity, not by time.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Any authorized cleanup of bad/polluted data in a live store (test
pollution, duplicate records, a known-bad batch) that will delete or
mass-correct rows.

## The rule

Time-window deletes are identity-blind. A filter like "rows created
between timestamp A and timestamp B" assumes the window contains only the
bad data — but a live system can have legitimate activity land inside the
exact same window (a scheduled job, a real user action, a concurrent
process), and a time filter cannot distinguish them from what you're
trying to remove. The window doesn't know which rows are bad; it only
knows when they were written, and "when" is not the same as "why."

**Scope destructive cleanup by exact identity instead:**

- Unique IDs of the specific bad records, when known.
- A known-bad payload signature or value (a specific fabricated
  identifier pattern, a specific malformed field) that only matches the
  actual pollution.
- A verified, explicitly enumerated list of rows, built by first querying
  for candidates and reviewing the list before deleting.

**If a time filter is genuinely unavoidable** (no better identity signal
exists), don't run it blind: enumerate exactly which rows it will affect
first (a `SELECT` before the `DELETE`, or equivalent), and eyeball that
list against what legitimate activity should look like in that window
before committing to the delete. The enumeration step is what turns a
blind time-window delete into something closer to identity-scoped — it
makes you look at what you're actually about to remove instead of trusting
the window's boundaries.

## Anti-pattern

Writing a cleanup query with only a time range and no review step, on the
assumption that "nothing legitimate happens in this exact window." Live
systems have scheduled jobs, retries, and background processes that don't
respect a human's mental model of "nothing was running then." If recovery
after an over-broad delete requires reconstructing a row from its
surviving related records, that's a sign the scoping should have been
tighter from the start — treat that as a near-miss worth tightening the
process over, not just a one-time inconvenience.

## Deduplication vs. portfolio exposure partitioning

Data identity and portfolio exposure are fundamentally distinct dimensions:
- **Exact observation duplicates** (same contract, line, event): Retain the latest valid pregame observation; deduplicate by exact contract identity.
- **Legitimate alternate contracts** (different lines/prices for same event): Must remain distinct in raw evidence.
- **Correlated exposure families** (line ladders/multiple bets on one event): Do NOT perform retroactive identity deletes on historical evidence. Enforce a prospective single-line/max-exposure sizing policy before decisions are made.

Cleanup plans must classify rows into these three cohorts with survivor rules based strictly on pre-decision fields and timestamp consistency.

## Rebuild generated environments instead of materializing corrupt placeholders

When cloud-synced storage (e.g. iCloud File Provider, OneDrive) contains broken or un-materialized placeholders in generated dependency trees (e.g. `venv`, `node_modules`):
- Do not execute recursive copies or atomic moves across the placeholder tree (which will block or thrash disk I/O trying to download dead files).
- Extract and verify the dependency manifest (`requirements.txt`, `package.json`) from readable metadata.
- Reconstruct the environment fresh outside the synced root.
- Verify parity and imports before replacing the original path with a compatibility link.

## Stake-normalize economic signatures in cross-tier audits

When auditing duplicate or conflicting records across multiple tiers (e.g. flat benchmark vs Kelly sizing):
- Normalize away dimensions that differ by design (e.g. stake sizing, display precision).
- Compare economic signatures stake-normalized ($P\&L / \text{units}$) at the storage precision rather than raw $P\&L$.
- Treat only result or quote differences as genuine conflicts; do not manufacture false identity conflicts from stake sizing differences.

## Pre-mutation backups and parse-before-merge for serialized payloads

When mutating records with serialized JSON-string columns:
1. **Take backups BEFORE mutating, never after.** A backup taken after the mutation backs up the corruption.
2. **Parse-before-merge:** Parse serialized JSON strings into native objects before extending or updating fields. Merging into the parsed structure prevents dropping existing unparsed keys.
3. **Superset assertion:** Assert that the post-mutation payload keys/fields form a strict superset of the pre-mutation payload before committing.

## Pre-flight check

Before running any destructive cleanup or mass data mutation:
1. Confirm the scope is identity-based (specific IDs, a specific bad-value signature, or a reviewed enumerated list) rather than purely time-based.
2. If deduplicating, distinguish exact duplicates from alternate contracts and correlated exposure ladders.
3. For cloud-synced generated folders, rebuild from metadata rather than materializing corrupt trees.
4. For cross-tier auditing, compare stake-normalized signatures at store precision.
5. Create a pre-mutation backup BEFORE touching data, parse serialized payloads before merging, and assert superset payload preservation.
</content>
