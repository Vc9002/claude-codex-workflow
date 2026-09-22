---
name: shell-gate-scripting
description: Any gate/wrapper script built around a report-producing CLI must check the wrapped CLI's real exit-code semantics before trusting them, and parse a verdict field directly when the exit code isn't authoritative. Use when writing any shell script that gates on another tool's output (CI checks, integrity verifiers, overlap/consistency checks).
---

# Shell Gate Scripting (internal)

Internal note. A short rule for writing gate/wrapper scripts around
another CLI's output.

## The rule

Some CLIs report their real verdict in structured output (JSON, a status
field) while always exiting 0 regardless of outcome — exit code 0 means
"the tool ran," not "the check passed." A gate script that trusts `$?`
without checking will pass a broken/failing state as green.

**Before wiring any gate/overlap/integrity script around a report-producing
CLI:**

1. Check the wrapped CLI's actual exit-code semantics first — grep its
   entrypoint for the return path, or just run it against a known-bad
   input and check `$?`.
2. If the exit code isn't authoritative, parse the verdict field directly
   (e.g. `chain_intact`, `status`, `ok`) from its structured output instead
   of trusting `$?`.
3. Only rely on exit code alone once you've confirmed it actually reflects
   the check's real outcome.

**Principle:** a gate is only as honest as the weakest signal it trusts —
exit codes are a convention some tools follow and some don't; verdicts in
structured output are data. Verify which one actually carries the truth
before building automation on top of it.

## Related note

When editing a file that a gate script also touches, mid-session, in a
repo where other sessions/agents might be writing concurrently: re-read the
file immediately before a multi-edit sequence if there's any hint of
parallel writers (an edit-tool on-disk-change warning, a recent unexpected
mtime). Cheap insurance against clobbering a concurrent addition.

## Pipe-test before wiring in, including the pass-through cases

Visual review is not enough — a script that parses cleanly can still fail
at runtime, or fail to guard anything at all. Before wiring any new gate
script into `settings.json`, a hook, or CI:

1. **Watch for lexer-sensitive metacharacters in inline patterns.** A bare
   `>` or `<` inside an inline `[[ "$x" =~ ... ]]` regex is lexed by bash as
   redirection, not as a regex character, and throws a syntax error at
   runtime that visual review won't catch. Store any regex containing these
   characters in a variable first and test `[[ "$x" =~ $re ]]`, never inline
   it.
2. **Pipe-test with synthetic stdin before wiring the script anywhere**,
   checking both exit code AND the real side effect (not just "it didn't
   error"). Do this before the script is referenced from any config.
3. **Verify every external binary a script depends on** with `command -v`
   before trusting an "automatic" claim (e.g. a formatter a hook assumes is
   on PATH) — especially for adapted third-party/community scripts.

## Command-guard pattern design: two-layer matching, not substring case patterns

Block-lists for destructive commands (DROP TABLE, rm -rf, force-push) need
more than a keyword search:

- **`case` substring patterns are the wrong tool.** They block routine
  commands that merely mention the keyword (a grep, an echo string) and
  still miss real invocations where the keyword doesn't sit at a clean
  word boundary.
- **Anchoring to statement-start alone under-matches.** A destructive
  keyword following a quote (e.g. `sqlite3 db "DROP TABLE users"`) is a
  real invocation but isn't at statement-start.
- **The fix is two layers, ORed together:** (a) actor-anchored — a known
  database-client invocation (sqlite3/psql/mysql/mariadb/sqlcmd) containing
  the destructive keyword anywhere in its arguments, OR (b) statement-anchored
  — the keyword at a statement position (start of command, after `;`, after
  a newline in heredocs). Apply the same anchored-regex-with-boundaries
  treatment to `rm`/`git` guards instead of `case` substrings.
- **Test the pass-through cases as deliberately as the block cases.**
  Calibrate against routine commands that must NOT be blocked (`rm -rf
  ./dist`, `rm -rf ~/x`, force-with-lease pushes) alongside the destructive
  ones that must.

**Principle:** A block-list is only as good as its false-positive/false-negative
calibration — match the actor (which tool executes the statement) as well as
the action, and pipe-test the cases that must pass as deliberately as the
cases that must be blocked. Syntax that parses is not syntax that runs.

## Multi-stage pipelines: aggregate all child exit codes before green

When a supervisor script orchestrates multiple sequential or parallel child stages (e.g. data capture, feature compilation, model forecasting, ledger settlement, summary generation), checking only a subset of child exit codes allows silent partial crashes to pass as overall pipeline success.

**The final exit gate must evaluate the strict conjunction of every material stage:**
```bash
# Capture exit codes from all critical stages
run_stage1; S1=$?
run_stage2; S2=$?
run_stage3; S3=$?

# Assert conjunction — fail if ANY material stage failed
if [[ $S1 -ne 0 || $S2 -ne 0 || $S3 -ne 0 ]]; then
  echo "PIPELINE FAILED: Stage exits S1=$S1 S2=$S2 S3=$S3" >&2
  exit 1
fi
```
Never allow later reporting stages or simple file writes to mask an earlier forecasting or compute crash.

## Pre-flight check

Before deploying any shell gate or supervisor script:
1. Verify the wrapped CLI's true exit code semantics vs structured output status.
2. Ensure the final gate aggregates exit codes from ALL material child stages.
3. Pipe-test inline regexes and command guards with synthetic input to verify pass-through vs blocked execution.
4. Verify regression fingerprints key on content `(file, rule, message)`, not shifting line numbers.
