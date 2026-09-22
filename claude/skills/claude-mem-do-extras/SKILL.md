---
name: claude-mem-do-extras
description: Delta guidance for claude-mem's `do` skill (a plugin-owned, non-editable skill) — how to choose the mutation path when repairing domain data that has its own invariants (ledgers, audit chains, lifecycle guards). Load alongside `do` whenever an implementation phase involves fixing or backfilling live data.
---

# claude-mem:do — repair-path addendum (internal)

Internal note. `claude-mem:do` (plugin `thedotmack`) executes phased
implementation plans but doesn't prescribe how to choose *between* mutation
paths when a phase involves repairing or backfilling data in a system that
already encodes its own invariants. This file is that addendum — load it
alongside `do` whenever a plan phase touches live domain data (ledgers,
databases, any store with an audit trail, dedupe rule, or lifecycle state
machine).

## The rule

Before writing a raw-file or raw-SQL fix for domain data, grep the owning
class for existing sanctioned mutation methods — names like `archive*`,
`correct*`, `recompute*`, `reconcile*`, `settle*` on the class that owns the
data. Use one of those if it exists. Only fall back to direct file/DB edits
when no sanctioned path exists for the specific repair needed.

**A sanctioned method with zero call sites is a green light, not a dead
end.** An unused method that does exactly what you need was very likely
built for this and never wired up — that's still the correct path, not a
sign to avoid it.

## Why

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

## Checklist for a repair phase

1. Identify the class that owns the data being repaired.
2. `grep` that class (and its module) for `archive`, `correct`, `recompute`,
   `reconcile`, `settle`, `revert` — anything that reads as a lifecycle or
   correction verb.
3. If found: use it, even if it has no existing callers.
4. If genuinely absent: do the raw edit, but re-run whatever integrity/audit
   check the system has (chain verifier, reconciliation script) immediately
   after, in the same phase — don't defer verification to a later phase or
   assume it's fine because the edit "looked right."
