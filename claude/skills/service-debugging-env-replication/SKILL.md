---
name: service-debugging-env-replication
description: Debugging or verifying a service that runs under a scheduler (launchd, systemd, cron) — replicate the scheduler's real environment for live diagnostics, never for the test suite unless its docs say to, and verify a job actually did its work (concrete before/after state diff) rather than trusting a status query or exit code. Use whenever investigating a scheduled/background job's behavior.
---

# Service Debugging via Environment Replication

**Created by Vincent Chen**

Three related rules for debugging services that run under a scheduler,
where "run the same command by hand" quietly tests a different system than
the one actually in production.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Investigating a launchd/systemd/cron-scheduled job: a diagnostic CLI
returning suspicious output, a test suite behaving differently than
expected, or verifying that a scheduled job actually does what it's
supposed to after a change.

## Rule 1 — replicate the service's real environment for diagnostics

A scheduler's unit definition (launchd plist, systemd unit, crontab line)
often sets environment variables the service's code depends on for path
resolution — a runtime root, a repo root, a data directory. Code with a
silent fallback (defaulting to a repo-local path when the env var is
absent) can produce a completely different, plausible-looking answer when
run by hand without that environment — split-brain state where a
"diagnostic" reads one database and the live service writes another.

**Before trusting any read-only diagnostic's output on a scheduled
service:** read the scheduler's actual unit definition, extract its full
environment block, and run the diagnostic command with the identical
environment. Silent env-dependent fallback paths in the code under test are
themselves worth flagging as a bug class — they're what makes this failure
mode possible.

## Rule 2 — but NOT for the test suite, unless its docs say to

This cuts the other way from Rule 1, and both are easy to get backwards.
A repository's test suite has its own documented invocation — and tests
that pin "the default behavior when the env var is absent" will break, not
reveal a bug, if you inject the service's live environment into a test run
that was never meant to see it. Copying the scheduler's env into a
diagnostic CLI run is correct; copying it into `pytest` (or equivalent)
without checking the docs first tests a different system and produces
false regressions.

**Rule of thumb:** read the repo's documented test invocation before
running the suite in any service-heavy codebase. Environment replication is
for live diagnostics against production-shaped state, not for the test
suite, unless the suite's own documentation says to run it that way.

## Rule 3 — verify a job by its side effect, not its status

Two related failure shapes, both hiding behind "looks fine":

- **A scheduler's label and its exit code are unverified claims.** A job
  named for what it's supposed to do can silently invoke a *different*
  script or pipeline than its name and docs claim — it exits 0, produces
  plausible-looking output, and the mismatch stays invisible until the
  expected side effect (new rows in a specific database, a specific file's
  timestamp) is checked and found missing. Read the script the job
  actually invokes end to end, not just its plist/unit file and docs.
- **"Loaded"/"running" is not "correct."** `launchctl print` (or the
  systemd/cron equivalent) reporting a job as loaded only proves the
  process exists — not that its logic is right, especially right after a
  rewrite. A filter bug (reading the wrong config path, always resolving
  to an empty list) can make a job silently no-op, or silently do MORE
  than intended, while every status query says "healthy."

**Verification pattern that catches both:** before declaring a scheduled
job verified, (1) define the expected side effect in advance — a specific
row count, a specific file's timestamp, a specific state value — (2)
kickstart/trigger the job once, (3) diff that concrete artifact from
immediately before to immediately after. A liveness/status query alone
proves the process exists; only the before/after diff proves it did its
actual job. This generalizes past schedulers to CI triggers, webhooks, and
feature flags — anywhere something sits between "configured" and
"actually correct," force one real execution and diff state rather than
trusting a status field.

## Pre-flight check

Before reporting a scheduled-job investigation as complete, confirm: (1)
any diagnostic command's output was produced with the service's real
environment, explicitly read from its unit definition; (2) any test-suite
run used the repo's documented invocation, not an ad hoc environment; (3)
"verified" claims cite a concrete before/after state diff, not just a
status query result.

## Rule 4 — confirm the client's actual route before debugging a suspected service

Before replicating a suspected service's environment at all, confirm the
failing client is actually talking to that service. For a routed/proxied
client, capture the client process's own full command line (`ps aux` or
equivalent) first — wrapper-injected settings (per-session routing flags,
base-URL overrides) live there and are the ground truth for which backend
actually received the failing requests. Probing the suspected service
first, before checking the client's route, risks debugging a healthy
system while the real backend goes unexamined.

**Principle:** For a routed/proxied client, its own process environment is
the authoritative record of where its requests went — confirm the route
from the client side before debugging the destination.

## Rule 3 addendum — a scheduler-observer pair must share the locality convention

When a scheduler/planner and its observer/collector both consume the same
external API but compute dates independently, a locality mismatch (one
uses UTC-today, the other buckets by each event's local date) makes the
scheduler wake the observer at the wrong time — silently and permanently
losing non-backfillable data (e.g. final pregame state for late events).
Add this to the Rule 3 verification pattern: state each script's timezone
convention for the observed API explicitly, and cross-check the planner's
output date against the observer's date computation for the same event —
treat "nothing to do" from a quiet observer as a possible convention
mismatch, not automatically as success.

## Rule 5 — verify service shutdown across every runtime layer

A service's CLI reporting daemons stopped or a teardown command returning exit
code 0 is not proof of shutdown. KeepAlive launchd jobs, cron entries, or
detached worker containers (e.g. tmux sessions) can remain actively running.

**Treat shutdown as a multi-layer conjunction to independently verify:**
1. Supervisor labels are persistently disabled and unloaded (`launchctl disable` / `launchctl bootout` or systemd equivalents).
2. No loaded jobs exist in the supervisor (`launchctl list | grep <label>`).
3. No matching background processes exist in the process table (`pgrep -f`).
4. No orphan worker containers or tmux sessions remain active (`tmux ls`).
5. The CLI continues to function cleanly for manual execution.

## Rule 6 — verify the effective population of diagnostic checks

A command-line path filter is not proof of diagnostic scope. Diagnostic tools
(such as File Provider consistency checks, database integrity tools, or log
parsers) may print a target subpath in their header while scanning an entire
containing domain (>80k items).

**Before attributing diagnostic failures to a target directory:**
1. Record and compare the total number of evaluated items against the target tree.
2. Distinguish domain-wide snapshot mismatches from directory-local defects.
3. Use exact path-keyed cohort queries to evaluate localized repairs.

## Rule 7 — treat rapidly growing logs as evidence of a supervisor crash loop

When error logs in synced or local storage grow rapidly (>100MB) without stable
running writer processes, point-in-time process lookups will miss short-lived
children.

**When logs grow continuously:**
1. Inspect supervisor configuration, launchd plists, and respawn/KeepAlive policies.
2. Verify configured executable paths and working directories for typos or missing binaries.
3. Stop and persistently disable broken jobs before moving or clearing logs.
4. Fix or disable the supervisor loop before treating storage, sync, or disk space as the primary defect.

## Rule 8 — combine stack sampling with open-file/lock attribution for CPU-bound Python services

Native stack sampling proves a process is CPU-bound but often exposes only
interpreter frames for a Python service, with no Python function names to
attribute the hot path to.

**Fallback diagnostic sequence when native sampling can't resolve Python
frames:** (1) capture CPU and memory state, (2) take a short native stack
sample to confirm which thread is hot, (3) inspect the process's open
files and lock markers (`lsof`, flock state) and map them back to the
source-level critical section they belong to. Treat lock ownership as
attribution *evidence*, not proof — corroborate it against the invoked
code path and the live workload size before naming a root cause (e.g.
repeated full-file serialization on a specific ledger).

## Pre-flight check

Before reporting a scheduled-job or service investigation complete, confirm:
1. Diagnostic commands used the service's real environment read from its unit definition.
2. Test runs followed documented repository test invocations.
3. Verification cites concrete before/after state diffs.
4. Routed client commands (`ps aux`) were verified before debugging backend services.
5. Schedulers and observers share explicit locality and timezone conventions.
6. Shutdown was verified across all supervisor, process, and container layers.
7. Diagnostic tool evaluation populations were verified against target scopes.
8. Growing logs were investigated for supervisor crash loops.
9. CPU-bound Python attribution combined stack sampling with open-file/lock
   inspection when native frames didn't resolve, and treated lock ownership
   as corroborated evidence, not proof.
