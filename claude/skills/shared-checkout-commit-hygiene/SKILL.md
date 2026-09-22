---
name: shared-checkout-commit-hygiene
description: Internal — a git working tree or handoff-doc naming scheme shared with parallel/concurrent sessions is a shared buffer, not private state. Stage commits by exact path (never `git add -A`/`commit -a`) and use collision-resistant filenames for session records. Use before committing in, or writing session/handoff files into, a repo that other concurrent sessions may also be touching.
---

# Shared Checkout Commit Hygiene (internal)

Two related failure modes observed in repos where multiple sessions
(interactive or automated) can run concurrently against the same working
tree.

## 1. Never sweep the whole working tree into your commit

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

## 2. "Next free filename" is not atomic under parallel writers

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
