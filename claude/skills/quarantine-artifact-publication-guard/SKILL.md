---
name: quarantine-artifact-publication-guard
description: After moving evidence into a quarantine/backups directory inside a repo, enumerate what the next push will transmit before pushing — quarantine is local evidence, publication is a separate decision, and *.db/*.sqlite/credential-shaped files are release blockers unless explicitly declared publishable. Use after any move-to-quarantine operation and before any push.
---

# Quarantine Artifact Publication Guard

**Created by Vincent Chen**

A pre-push guard: backing something up into a repository directory is not
consent to publish it.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

After any "move to quarantine/backups" operation inside a repo — or any
time operational artifacts (database files, state files, credentials) have
been written into a directory that is about to be committed or pushed to a
remote.

## The rule

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

## Pre-flight check

Before pushing: the transmit list was enumerated, no database/credential-
shaped file is in it without explicit user sign-off, and the gitignore
rule for the quarantine directory was added in the same change as the
directory itself.

**Principle:** quarantine preserves evidence locally; publication is a
separate decision. Quarantine dirs should be local-only by default.
