---
name: parallel-agent-hygiene
description: "Working with parallel agents or concurrent sessions on one shared checkout: disjoint-file fix orchestration, exact-path staging and collision-resistant handoff filenames, and delegating review of uncommitted changes to subagents without worktree isolation. Use before fanning out agents, committing in a shared tree, or reviewing uncommitted diffs."
---

# parallel-agent-hygiene

Consolidated from: parallel-fix-orchestration, shared-checkout-commit-hygiene, uncommitted-diff-review. Each section below is the original skill, unchanged apart from heading level.

---

<!-- from skill: parallel-fix-orchestration -->
## Parallel Fix Orchestration

**Created by Claude, distilled from the operator's real session observations.**

Coordinates several agents fixing a codebase concurrently in one shared
working tree. Originated from a real incident: four parallel fix agents
with disjoint file ownership produced no write conflicts, yet a
cross-agent semantic coupling still left a red test that only the final
integration run caught.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** If questions arise about the methodology, or the
user gives constructive feedback on output derived from this skill, route
it to the operator of the workspace where this skill is installed. (No
public repository exists yet — do not add a repository link until one
does.) If feedback stems from the agent not following the skill's rules,
acknowledge and correct.

### When to use

A fix pass over many files that the user wants done in parallel (or that
benefits from parallel review), where multiple agents will edit the same
checkout in the same session.

### The three rules

1. **Disjoint file ownership.** Give every agent an explicit allow-list of
   files it may edit. Everything else is read-only — instruct "report,
   don't edit" for shared files. File-level isolation prevents write
   conflicts — and nothing more.
2. **Assign shared-state tests up front.** Before partitioning, identify
   which tests pin shared state (the real shipped config, artifact paths,
   golden files, env-sensitive defaults) and assign each to the agent that
   owns that state. Otherwise one agent fixes a config while another pins
   a test to its old value.
3. **The full suite is part of the plan.** Cross-agent couplings are
   invisible to per-agent targeted runs. The final step is always one full
   test-suite run; any red test is routed back to its owning agent, and
   the integration-run output is what gets reported — not the sum of the
   agents' claims.
4. **Resume interrupted agents via SendMessage.** Distinguish agent failure
   modes by cause: infrastructure disruptions (e.g. host sleep, API connection
   drops, transient timeouts) do not erase the agent's internal state. Resume
   the interrupted agent using `send_message` rather than spawning a fresh agent
   that would have to reconstruct context from scratch. Instruct long-running
   agents to write durable intermediate checkpoints (disk files, stubs). Only
   unrecoverable task logic errors warrant a fresh agent spawn.

### Pre-flight

Before reporting "fixes complete":

- Re-run the FULL suite (not per-agent subsets) and capture the output.
- If red, route each failure to the owning agent before declaring done.
- Report the integration-run result verbatim, including any failures.

### Anti-patterns

- Allowing two agents to edit the same file, or "whoever gets there
  first" ownership.
- Targeted per-agent test runs presented as the integration result.
- Reporting agent-completion messages as the pass's outcome — the pass's
  outcome is one green full-suite run.

### Consolidation refactors (single source of truth)

A related but distinct task: collapsing N parallel configs/registries/code
paths that have drifted into one canonical source, rather than fixing bugs
across a fixed file set. Originated from a real incident: a config file
listed many allowed entries but the validator, health check, and server
only ever touched one of them — a "split personality" invisible until
someone read the config against the code that consumed it.

The pattern that worked, in order:

1. **Identify the keystone.** Find the one artifact (a config file plus its
   validator, a schema plus its loader) whose drift is causing the split
   personality. That's what the new module becomes the source of truth for.
2. **Build one new module, don't reimplement in parallel.** Give it
   fail-closed validation per entry (a broken secondary entry gets disabled
   with a recorded error; a broken primary entry raises) — classify this
   explicitly in the data contract, don't leave it implicit.
3. **Preserve the legacy public API via delegation, not reimplementation.**
   The old module keeps its function signatures AND its exact
   error/exception message strings if existing tests assert on them —
   internally it just calls the new module. Reimplementing the old surface
   in parallel guarantees drift between "the config," "the validator," and
   "the server" all over again.
4. **Migrate the real checked-in config in the same commit** the new module
   lands, with the legacy schema's derivation path still implemented and
   tested — so no consumer breaks mid-migration.
5. **Pin the real checked-in config as a test fixture, not just a
   `tmp_path` fixture.** The highest-value test is not unit-level: load the
   actual file that ships and assert every entry in it resolves. A
   contract requirement (e.g. "every listed entry must be valid") becomes a
   test before it becomes a CI step, and it catches drift the moment new
   entries are added.

Anti-pattern specific to this mode: adding the new source-of-truth module
alongside the old one without making the old one delegate — now there are
two places that can each be "right," and nothing forces them to agree.

---

<!-- from skill: shared-checkout-commit-hygiene -->
## Shared Checkout Commit Hygiene (internal)

Two related failure modes observed in repos where multiple sessions
(interactive or automated) can run concurrently against the same working
tree.

### 1. Never sweep the whole working tree into your commit

A parallel session (another interactive session, or an automated
auditor/observer) can leave uncommitted edits in the shared checkout —
doc updates, generated files — that are real and correct for that other
session's work, just not yet committed by it. `git status --short` showing
files you didn't touch is evidence of a concurrent writer, not clutter.

- Before any commit, run `git status --short` and compare it against the
  list of files *this* session actually edited.
- Stage those exact paths explicitly (`git add path/to/file ...`) — never
  `git add -A` or `git commit -a`, both of which implicitly claim
  authorship over every uncommitted change in the tree, including another
  session's half-finished work.
- If foreign modifications appear, leave them untouched and note them in
  your handoff so their owning session can commit them.

**Principle:** in a shared checkout, the working tree is a shared buffer.
An unqualified "stage everything" is an implicit authorship claim over
other sessions' uncommitted work. Explicit path staging is the pre-commit
authorship check.

### 2. "Next free filename" is not atomic under parallel writers

Repo conventions that pick the next free suffix for session/handoff files
(e.g. `HANDOFF_<date>-a`, `-b`, `-c`, ...) race when two concurrent
sessions both compute the same "next free" name and write to it — the
later `Write()` silently replaces the earlier session's file with no
conflict error, no merge, just a vanished record. Recovery, if it happens
at all, depends on the earlier session still holding the content in its
own context.

- Prefer filenames that include a stable, session-specific identifier
  (e.g. a start-time timestamp: `HANDOFF_YYYY-MM-DD-HHMM`) rather than a
  short next-free-letter suffix.
- Before writing a session-record file under a shared naming convention,
  read for an existing file at the candidate name; if one exists, treat it
  as evidence of a concurrent writer and pick a distinct name rather than
  overwriting.

**Principle:** "next free filename" is a check-then-write race under
parallel writers regardless of how the free slot is computed. Session
records need collision-resistant names, or they only survive as long as
someone's context still holds the content.

---

<!-- from skill: uncommitted-diff-review -->
## Uncommitted Diff Review

**Created by Vincent Chen**

Rules for delegating review of *uncommitted* changes to subagents, where
the default agent-isolation mechanism (a separate worktree) silently breaks
the review by hiding the very changes being reviewed.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

### When to use

Fanning out two or more review/analysis agents over a diff (or a large set
of edits) that exists only in the working tree — not yet committed.

### The rule

1. **Forbid worktree isolation for this task.** A subagent given an
   isolated git worktree only sees committed history — uncommitted changes
   in the shared checkout simply don't exist from its point of view. An
   agent asked to review "the current changes" from inside a worktree will
   either find nothing, or (worse) review stale committed code and report
   findings that don't apply to what's actually being changed. Explicitly
   instruct each review agent to operate against the shared checkout path,
   not a worktree.
2. **Name the exact shared path.** Don't rely on an agent inferring where
   the real working tree is — state it explicitly, and give the diff
   command to run against it (e.g. `git diff HEAD -- <path>` for a bounded
   file set, or `git diff HEAD` for everything).
3. **Give each agent a bounded file list.** Split the diff across agents by
   file or module so their attention is focused and their findings are
   comparable in scope.
4. **Require file:line plus a concrete failure scenario per finding.** A
   claim like "this function has a bug" is not actionable; "line 142:
   `locals()` is assigned to but never used, so the intended mutation is a
   no-op" is. Push agents toward the latter.
5. **Spot-verify the highest-severity claims yourself before reporting
   them onward.** Subagent findings on uncommitted code are claims, not
   verified results — they were produced under time and context pressure
   like any other agent output. Before passing findings to the user (or
   into a fix pass), open the file yourself and confirm the one or two
   sharpest claims are real.

### Anti-patterns

- Letting a review agent default to its own isolated worktree "for safety"
  — it silently reviews the wrong (or no) code.
- Treating an agent's finding as settled because it cited a file and line
  — a plausible-sounding claim with a real citation can still be wrong;
  spot-verification is what separates a claim from a result.
- Giving every agent the entire diff with no partition — findings overlap,
  attention is diluted, and comparing severity across agents becomes noisy.

### Pre-flight check

Before dispatching a multi-agent review of uncommitted work, confirm the
brief given to each agent: (1) explicitly forbids worktree isolation and
names the shared checkout path, (2) includes the diff command to run, (3)
bounds the file list, (4) requires file:line + failure scenario per
finding. Before reporting results onward, confirm the highest-severity
claims were independently checked against source.

### A worktree hazard also applies to test runs, not just review agents

The same worktree-isolation hazard this skill documents for review agents
also breaks test runs: a git worktree sharing a venv with the main checkout
via an editable install silently imports the MAIN checkout's source, so a
test run inside the worktree can pass green while testing the wrong tree
(invisible for modified files; only visible as an import error for new
ones). Before trusting "N tests passing" for any worktree or secondary
checkout, verify the imported module's `__file__` resolves under that
checkout, not just that the process exits 0.

### Format hooks can hijack a commit's boundary

A pre-commit formatter operates on the whole file, not on the lines being
changed. If the target file already has format drift, the hook will
reformat the entire file on the next commit that touches it — turning a
small, reviewable diff into hundreds of lines of unrelated churn, or (if
the hook then fails on pre-existing lint findings) leaving that rewrite on
disk while reporting only the lint failure, silently inflating whatever
commit comes next.

**Before committing a small fix to a file with known drift:** check
`ruff format --check` (or equivalent) on the target file first. If it's not
clean, either do a dedicated format-only commit first, or commit the
intended fix with `--no-verify` and verify purity at the **token** level
(whitespace-stripped equality), not with `git diff -w` (which can't see
newline restructuring). After ANY failed hook run, re-check `git diff
--stat` before retrying — never assume the working tree is unchanged from
what you left; if the formatter already rewrote lines outside the intended
change, restore from HEAD and re-apply the intended edit rather than
committing the combined result.

**Principle:** A formatting hook's unit of work is the file; a commit's
unit of meaning is the change. When those disagree, a failed hook run can
quietly convert a reviewable diff into an unreviewable one, and the growth
is invisible unless you re-measure before retrying.
