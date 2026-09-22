---
name: compaction-safe-digests
description: Long read-heavy tasks (digesting many files, building a structured summary) must checkpoint progress to durable disk state after each batch, because in-context state — including the in-progress digest itself — is not reliably preserved across a context compaction. Use for any task expected to span a compaction boundary.
---

# Compaction-Safe Digests

**Created by Vincent Chen**

One rule for long, read-heavy tasks: don't trust the in-context summary to
survive a compaction. Mirror progress to disk as you go, so a compaction
that drops your working state leaves a recoverable record instead of
forcing a full redo.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Any task that reads many files (tens or more) to build a structured digest,
inventory, or synthesis, and is long enough that a context compaction is a
real possibility before the task finishes.

## The problem

A compaction summarizes the conversation to free context space. It is
built to preserve the gist of what happened, not to guarantee an
in-progress structured artifact (a partial digest, a running list of "files
read and what they contained") survives intact. In practice, in-progress
structured state is exactly the kind of thing a compaction summary tends to
drop or compress lossily — it looks like it should be recoverable from the
transcript, but the transcript itself is often not a reliable recovery
path either (tool-call history can be summarized away too).

The costly failure mode: after compaction, the agent re-reads everything
already digested because the rule in effect was "prior digests are only
authoritative if they survived into the summary" — and if they didn't,
the only safe move looks like starting over. On a task with dozens of
files, that's a full duplicate pass.

## The rule

**Checkpoint to disk after every batch**, not just at the end. A bounded
progress file in the workspace — one line per file: path, a cheap fact
that proves it was actually read (line count, byte size), and a one-line
status/summary — turns "trust the in-context summary" into "trust a file
that's still there no matter what happens to the context." Write it
incrementally as you go, not as a single write at the end (the end may
never be reached before a compaction, or before a session interruption).

**On resume after a compaction:** read the checkpoint file first. Treat it
as the authoritative list of what's already done. Re-process only items
whose checkpoint entry is verifiably absent or incomplete — don't re-read
everything just because the in-context digest feels uncertain. If the
checkpoint file says a file was already processed, trust that over a
fuzzy memory of "did I get to that one."

## Anti-pattern

Relying on "I'll remember where I was" or on the compaction summary to
carry forward a structured, itemized digest. A compaction summary is
prose-shaped; a progress checklist is line-shaped. Don't ask a
summarization mechanism to preserve exact structured state — write the
structured state yourself, to a place a summarization pass can't touch.

## Pre-flight check

Before starting a long read-heavy task, decide on the checkpoint file's
path and format up front. After each batch, confirm the checkpoint file
was actually updated (not just planned) before moving to the next batch.
On any resume, confirm the checkpoint was read and used to scope remaining
work before re-reading anything.
