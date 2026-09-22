---
name: cloud-to-local-migration
description: Resolve the human-facing canonical location before migrating a cloud-backed system (tracker, database, doc) into a local file and repointing services/skills/scheduled jobs to it. Use whenever moving a cloud service's data to a local replacement (spreadsheet, SQLite file, local doc) and wiring automation to it.
---

# Cloud-to-Local Migration

**Created by Vincent Chen**

A short discipline for migrating a cloud-backed system (a tracker, a
database, a synced doc) into a local file and repointing whatever depends
on it — services, skills, scheduled snapshots.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Any task that replaces a cloud/hosted system with a local file-based
equivalent and then wires automation (services, skills, scheduled jobs,
snapshot scripts) to read/write that file.

## The rule — resolve the human-facing location before wiring anything

There are two candidate locations for the new local file, and they are
easy to conflate:

1. **The machine-facing state path** — wherever internal config or a
   service definition already points, or wherever automation can most
   conveniently reach.
2. **The human-facing working folder** — where the user actually works
   with files of this kind day to day (their own named folder for this
   domain, not an internal state directory).

Creating the first technically coherent file in the machine-facing
location, then wiring services to it, produces a file that "works" but is
hard for the user to find, edit, or recognize as canonical — forcing a
second migration once the mismatch surfaces.

**Before creating the local replacement:**
1. Resolve the human-facing working folder first — check where the user
   already keeps files of this domain (ask, or look for an existing named
   folder), not just where config or automation currently points.
2. Choose the human-facing location as canonical. Create the new file
   there.
3. Only then wire services, skills, and scheduled snapshots to the
   resolved canonical path. If something machine-facing genuinely needs a
   different path, use a compatibility link *to* the canonical file rather
   than making the machine-facing copy authoritative.

**Anti-pattern:** inspecting the service configuration or scheduler
definition first, building the replacement at whatever path it names, and
only discovering the user's real working folder afterward. This produces a
file that is technically wired correctly but functionally lost to the
user — the fix is a second, avoidable migration.

## Pre-flight check

Before creating any local replacement file, confirm: (1) the user's actual
human-facing working folder for this domain has been located (not
inferred from config); (2) that folder, not an internal state path, is the
target for the canonical file; (3) any machine-facing path that must also
resolve to this data does so via a link or read path pointing at the
canonical file, not a second copy.
