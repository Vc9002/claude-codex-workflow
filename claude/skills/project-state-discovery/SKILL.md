---
name: project-state-discovery
description: When a remembered file path, project location, or prior-session fact doesn't resolve (a 404, a missing directory), search for what actually changed before asking the user — glob for name variants, and prefer a project's own migration/move record over memory. Use at the start of any session that relies on a remembered path or prior-session state.
---

# Project State Discovery

**Created by Vincent Chen**

A short procedure for when persistent memory (notes from a prior session)
disagrees with the filesystem: verify before asking, and prefer the
project's own record of its history over a remembered snapshot.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

A remembered path from a previous session (a project directory, a config
file location) doesn't exist anymore, or memory otherwise disagrees with
observed state.

## The rule

Treat memory-derived paths and facts as leads to verify, not facts to act
on. When a remembered path 404s:

1. **Glob for name variants before asking the user.** Projects get renamed,
   moved, or have punctuation changed (a space becomes a dash, a suffix is
   dropped). A quick directory listing one level up, or a glob on a
   distinctive substring of the old name, often finds the new location
   without needing to interrupt the user.
2. **Prefer a project-written record over memory.** Well-run projects that
   move or restructure themselves sometimes leave their own record of it —
   a migration manifest, a `MOVED.md`, a changelog entry naming old and new
   paths, old and new identifiers (git SHAs, version tags), and what was
   carried over. If one exists at the new location, read it before
   guessing or asking — it's authoritative about what happened and why,
   where memory is only a snapshot of what was true when it was written.
3. **Update the memory record once the true location is confirmed.** Don't
   leave the stale path in place for the next session to rediscover the
   same 404.

**Anti-pattern:** asking the user "where did the project go?" as the first
move. It's a reasonable fallback, but only after a quick glob and a check
for the project's own migration record have both come up empty — those
two checks are cheap and often sufficient on their own.

## Pre-flight check

Before reporting a path as missing or asking the user to relocate it,
confirm: a glob for name variants was tried, and any migration-style
record at the plausible new location was checked.
