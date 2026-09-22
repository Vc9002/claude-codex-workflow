---
name: config-flip-completion
description: When directed to flip a config flag or state value back on/off, the change isn't complete until tests that pin the OLD state are found and updated — grep for assertions on the real shipped config's value, not just the flag's runtime consumers. Use whenever an operator/user directive asks to reverse, re-enable, or restore a previous config or feature-flag state.
---

# Config Flip Completion

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

## When to use

An operator or user directive to flip a config value, feature flag, or
similar toggle back to a previous state (e.g. "turn X back on", "restore
the old default").

## The rule

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

## State-location flips move invariants, not just bytes

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

## Pre-flight check

Before reporting a state-flip directive as done, confirm: the flag value
changed, anything it gated was restored, the test suite was searched
specifically for assertions on the real shipped config's value (not just
flag consumers), those tests were updated, and the updated files were
re-run green. For a state-*location* flip specifically, also confirm:
machine-local test assertions (live-file-sync checks, reads of now-untracked
files) were found and either converted to synthetic fixtures or moved to a
documented operational checklist.
