---
name: uncommitted-diff-review
description: Delegating code review of uncommitted changes to subagents — forbid worktree isolation (they only see committed history and will produce stale or false findings against uncommitted work), name the exact shared checkout path, bound the file list, require file:line evidence, and spot-verify the highest-severity claims yourself. Use whenever fanning out review agents over a diff that hasn't been committed yet.
---

# Uncommitted Diff Review

**Created by Vincent Chen**

Rules for delegating review of *uncommitted* changes to subagents, where
the default agent-isolation mechanism (a separate worktree) silently breaks
the review by hiding the very changes being reviewed.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Fanning out two or more review/analysis agents over a diff (or a large set
of edits) that exists only in the working tree — not yet committed.

## The rule

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

## Anti-patterns

- Letting a review agent default to its own isolated worktree "for safety"
  — it silently reviews the wrong (or no) code.
- Treating an agent's finding as settled because it cited a file and line
  — a plausible-sounding claim with a real citation can still be wrong;
  spot-verification is what separates a claim from a result.
- Giving every agent the entire diff with no partition — findings overlap,
  attention is diluted, and comparing severity across agents becomes noisy.

## Pre-flight check

Before dispatching a multi-agent review of uncommitted work, confirm the
brief given to each agent: (1) explicitly forbids worktree isolation and
names the shared checkout path, (2) includes the diff command to run, (3)
bounds the file list, (4) requires file:line + failure scenario per
finding. Before reporting results onward, confirm the highest-severity
claims were independently checked against source.

## A worktree hazard also applies to test runs, not just review agents

The same worktree-isolation hazard this skill documents for review agents
also breaks test runs: a git worktree sharing a venv with the main checkout
via an editable install silently imports the MAIN checkout's source, so a
test run inside the worktree can pass green while testing the wrong tree
(invisible for modified files; only visible as an import error for new
ones). Before trusting "N tests passing" for any worktree or secondary
checkout, verify the imported module's `__file__` resolves under that
checkout, not just that the process exits 0.

## Format hooks can hijack a commit's boundary

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
