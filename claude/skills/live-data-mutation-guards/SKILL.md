---
name: live-data-mutation-guards
description: "Pre-flight guards before mutating live data or config: scope destructive cleanups by exact identity not time window, enumerate quarantined evidence in published repo paths, pick the right mutation path for domain data with invariants (claude-mem do), and finish config flag flips by updating tests that pin the old state. Use before any delete, backfill, quarantine, or flag flip."
---

# live-data-mutation-guards

Consolidated from: destructive-cleanup-scoping, quarantine-artifact-publication-guard, claude-mem-do-extras, config-flip-completion. Each section below is the original skill, unchanged apart from heading level.

---

<!-- from skill: destructive-cleanup-scoping -->
## Destructive Cleanup Scoping

**Created by Vincent Chen**

One rule for authorized data cleanup: scope by identity, not by time.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

### When to use

Any authorized cleanup of bad/polluted data in a live store (test
pollution, duplicate records, a known-bad batch) that will delete or
mass-correct rows.

### The rule

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

### Anti-pattern

Writing a cleanup query with only a time range and no review step, on the
assumption that "nothing legitimate happens in this exact window." Live
systems have scheduled jobs, retries, and background processes that don't
respect a human's mental model of "nothing was running then." If recovery
after an over-broad delete requires reconstructing a row from its
surviving related records, that's a sign the scoping should have been
tighter from the start — treat that as a near-miss worth tightening the
process over, not just a one-time inconvenience.

### Deduplication vs. portfolio exposure partitioning

Data identity and portfolio exposure are fundamentally distinct dimensions:
- **Exact observation duplicates** (same contract, line, event): Retain the latest valid pregame observation; deduplicate by exact contract identity.
- **Legitimate alternate contracts** (different lines/prices for same event): Must remain distinct in raw evidence.
- **Correlated exposure families** (line ladders/multiple bets on one event): Do NOT perform retroactive identity deletes on historical evidence. Enforce a prospective single-line/max-exposure sizing policy before decisions are made.

Cleanup plans must classify rows into these three cohorts with survivor rules based strictly on pre-decision fields and timestamp consistency.

### Rebuild generated environments instead of materializing corrupt placeholders

When cloud-synced storage (e.g. iCloud File Provider, OneDrive) contains broken or un-materialized placeholders in generated dependency trees (e.g. `venv`, `node_modules`):
- Do not execute recursive copies or atomic moves across the placeholder tree (which will block or thrash disk I/O trying to download dead files).
- Extract and verify the dependency manifest (`requirements.txt`, `package.json`) from readable metadata.
- Reconstruct the environment fresh outside the synced root.
- Verify parity and imports before replacing the original path with a compatibility link.

### Stake-normalize economic signatures in cross-tier audits

When auditing duplicate or conflicting records across multiple tiers (e.g. flat benchmark vs Kelly sizing):
- Normalize away dimensions that differ by design (e.g. stake sizing, display precision).
- Compare economic signatures stake-normalized ($P\&L / \text{units}$) at the storage precision rather than raw $P\&L$.
- Treat only result or quote differences as genuine conflicts; do not manufacture false identity conflicts from stake sizing differences.

### Pre-mutation backups and parse-before-merge for serialized payloads

When mutating records with serialized JSON-string columns:
1. **Take backups BEFORE mutating, never after.** A backup taken after the mutation backs up the corruption.
2. **Parse-before-merge:** Parse serialized JSON strings into native objects before extending or updating fields. Merging into the parsed structure prevents dropping existing unparsed keys.
3. **Superset assertion:** Assert that the post-mutation payload keys/fields form a strict superset of the pre-mutation payload before committing.

### Pre-flight check

Before running any destructive cleanup or mass data mutation:
1. Confirm the scope is identity-based (specific IDs, a specific bad-value signature, or a reviewed enumerated list) rather than purely time-based.
2. If deduplicating, distinguish exact duplicates from alternate contracts and correlated exposure ladders.
3. For cloud-synced generated folders, rebuild from metadata rather than materializing corrupt trees.
4. For cross-tier auditing, compare stake-normalized signatures at store precision.
5. Create a pre-mutation backup BEFORE touching data, parse serialized payloads before merging, and assert superset payload preservation.
</content>

---

<!-- from skill: quarantine-artifact-publication-guard -->
## Quarantine Artifact Publication Guard

**Created by Vincent Chen**

A pre-push guard: backing something up into a repository directory is not
consent to publish it.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

### When to use

After any "move to quarantine/backups" operation inside a repo — or any
time operational artifacts (database files, state files, credentials) have
been written into a directory that is about to be committed or pushed to a
remote.

### The rule

1. **Make quarantine dirs local-only as part of the quarantine step.**
   Add gitignore rules for quarantine artifacts at the moment you create
   the directory (e.g. `backups/**/*.db` plus a quarantine-dir rule), not
   after a push has already exposed them. Keep the README tracked so the
   directory's purpose survives.
2. **Before any push, enumerate what it will transmit** (`git log --stat
   origin/branch..HEAD` or `git diff --name-only`). Treat any `*.db`,
   `*.sqlite`, or credential-shaped file as a release blocker unless the
   user has explicitly declared those specific files publishable.
3. **Rebuild rather than force-push if the blocker is already in history**
   — and if a force-push becomes unavoidable, it needs explicit user
   authorization; it is not a routine step.

### Pre-flight check

Before pushing: the transmit list was enumerated, no database/credential-
shaped file is in it without explicit user sign-off, and the gitignore
rule for the quarantine directory was added in the same change as the
directory itself.

**Principle:** quarantine preserves evidence locally; publication is a
separate decision. Quarantine dirs should be local-only by default.

---

<!-- from skill: claude-mem-do-extras -->
## claude-mem:do — repair-path addendum (internal)

Internal note. `claude-mem:do` (plugin `thedotmack`) executes phased
implementation plans but doesn't prescribe how to choose *between* mutation
paths when a phase involves repairing or backfilling data in a system that
already encodes its own invariants. This file is that addendum — load it
alongside `do` whenever a plan phase touches live domain data (ledgers,
databases, any store with an audit trail, dedupe rule, or lifecycle state
machine).

### The rule

Before writing a raw-file or raw-SQL fix for domain data, grep the owning
class for existing sanctioned mutation methods — names like `archive*`,
`correct*`, `recompute*`, `reconcile*`, `settle*` on the class that owns the
data. Use one of those if it exists. Only fall back to direct file/DB edits
when no sanctioned path exists for the specific repair needed.

**A sanctioned method with zero call sites is a green light, not a dead
end.** An unused method that does exactly what you need was very likely
built for this and never wired up — that's still the correct path, not a
sign to avoid it.

### Why

Systems with audit chains, hash-chained event logs, dedupe keys, or
lifecycle guards (draft → settled → archived, etc.) enforce those
invariants *inside* their own mutation methods, not as a database
constraint you can bypass and still trust. A raw edit fixes the visible
bytes and silently desyncs the invariant — an audit chain that no longer
verifies, a settled row with no correction event, a duplicate the dedupe
key was supposed to prevent. The break is often invisible until something
downstream (an integrity verifier, a reconciliation job) surfaces it later,
by which point the causal thread back to the raw edit is gone.

**Worked example (abstracted):** a project's ledger exposes
`Ledger.archive_rows(reason=...)` for moving out superseded records (with
audit-chain events and a required reason) and `Ledger.correct(row_id,
reason=...)` for fixing an already-finalized row. Both existed, unused, when
a repair task reached for direct spreadsheet-library cell edits instead.
Using the sanctioned methods kept the audit-chain verifier green and left a
per-row correction event; the raw-edit path would have passed silently and
broken verification only when the chain was later checked.

### Checklist for a repair phase

1. Identify the class that owns the data being repaired.
2. `grep` that class (and its module) for `archive`, `correct`, `recompute`,
   `reconcile`, `settle`, `revert` — anything that reads as a lifecycle or
   correction verb.
3. If found: use it, even if it has no existing callers.
4. If genuinely absent: do the raw edit, but re-run whatever integrity/audit
   check the system has (chain verifier, reconciliation script) immediately
   after, in the same phase — don't defer verification to a later phase or
   assume it's fine because the edit "looked right."

---

<!-- from skill: config-flip-completion -->
## Config Flip Completion

**Created by Vincent Chen**

A one-rule checklist for "flip this flag back" directives: the flag isn't
the whole change — the tests pinning its old value are part of the same
change, and get missed by scoping the work to "find where the flag is
read."

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

### When to use

An operator or user directive to flip a config value, feature flag, or
similar toggle back to a previous state (e.g. "turn X back on", "restore
the old default").

### The rule

A state-flip is not complete until every test asserting the *old* state is
found and updated to the new intent. The failure mode: flipping the config
value alone leaves the flag's read-sites working correctly, but any test
that separately asserts "the real shipped config has value V" now fails —
and if V was also gating something else (archived data, a disabled code
path), that something else needs restoring too, not just the flag.

**Complete procedure for a state-flip directive:**

1. Flip the config/flag value itself.
2. Restore whatever the flag was gating, if anything (archived data,
   disabled records, a suppressed code path) — the flag flip and the thing
   it controls are one change, not two.
3. **Grep the test suite for assertions on the real shipped config's
   value** — not just for the flag's consumers/call-sites, which is the
   scope people naturally reach for first. Search for the literal value,
   the flag name in assertion context, or the config file path used as a
   fixture.
4. Update those pinning tests to the new intended state.
5. Re-run just those files (not necessarily the full suite) to confirm
   green, then note in the report that pinning tests were found and
   updated — this is the step most likely to be silently skipped, so
   naming it in the report is part of the discipline.

**Why the distinction matters:** "grep for consumers of the flag" finds the
code that *reads* the flag and behaves differently based on it. It does
NOT find tests that assert what the flag's value *currently is* in the
real, checked-in config — those are a different grep target (the value or
the config fixture, not the flag's usage sites), and they're exactly the
tests that go red after a flip that only touched the flag itself.

### State-location flips move invariants, not just bytes

A related but distinct flip: moving *where* state lives (frozen vs. rolling
artifact, git-tracked vs. untracked data) rather than a value. This breaks
tests differently — a test that asserted "the shipped artifact is in sync
with live source data" pinned an invariant that has now moved off CI
entirely, onto the rolling artifact and the operator's machine. A second,
easy-to-miss class: tests reading files that just became untracked will
keep passing locally (the files still exist on disk) and only fail in CI's
clean checkout.

**When flipping a state-location contract:** grep tests for machine-local
assertions — "live file is in sync with artifact," reads of repo data files,
anything that implicitly depends on the operator's runtime root — and
convert them to either hermetic synthetic fixtures or a documented
operational checklist (e.g. a burn-in check), in the same change as the
flip. An invariant that used to be unit-testable can become an operational
property that must be re-homed, not silently left in a test that now tests
the wrong layer.

### Pre-flight check

Before reporting a state-flip directive as done, confirm: the flag value
changed, anything it gated was restored, the test suite was searched
specifically for assertions on the real shipped config's value (not just
flag consumers), those tests were updated, and the updated files were
re-run green. For a state-*location* flip specifically, also confirm:
machine-local test assertions (live-file-sync checks, reads of now-untracked
files) were found and either converted to synthetic fixtures or moved to a
documented operational checklist.
