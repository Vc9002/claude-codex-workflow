---
name: course-schedule-sync
description: Internal — syllabi are living documents, not fixed schedules; treat any Todoist/Canvas course-task sync as a diff-and-resync operation, not a one-shot rebuild. Use when creating, rebuilding, or updating course reading/assignment tasks from a syllabus.
---

# Course Schedule Sync (internal)

Every Fall 2026 syllabus this project has touched carries an explicit
mutability warning (CRIM: "Tentative Schedule — the final one is on
Canvas"; PHIL 1439: "course schedule and assigned readings are subject to
change"; LGST 2240: "MODULES readings subject to change"). A course-task
sync built as a one-shot rebuild treats the syllabus as a fixed snapshot,
so it silently rots the moment a professor posts an updated schedule on
Canvas — the task list only gets fixed when the drift is noticed by hand.

## Rules

1. **Treat every synced task list as a cache of a mutable source, not a
   final artifact.** Any session that touches course tasks should
   spot-check Canvas (syllabus page, announcements) for date changes
   before trusting the existing Todoist copy.
2. **Keep the rebuild/sync plan data**, not just the resulting tasks — a
   durable diffable record (e.g. a persisted JSON of parsed
   readings/dates per course) so a resync can diff-and-apply instead of
   rebuilding from scratch.
3. **Flag source disagreements instead of silently picking one.** When two
   syllabi (or a syllabus and Canvas) disagree on a date — e.g. one course
   says Fall Break is 10/1, another says 10/8 — surface the conflict to
   the user rather than guessing.
4. **Record provenance for estimated/undated items.** Some courses have no
   explicit dates in the syllabus (module-mapped schedules, TBA finals).
   When a date is inferred rather than stated, note where it came from so
   a later correction is easy to trace back to the assumption that
   produced it.

## Principle

A schedule-mutability warning in the syllabus means the task list must be
re-derivable, not just correct once. Build the sync so that "the schedule
changed" costs a diff, not a rebuild.
