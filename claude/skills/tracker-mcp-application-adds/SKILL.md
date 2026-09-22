---
name: tracker-mcp-application-adds
description: Add or patch job application rows in Vincent's Tracker MCP from pasted postings, public Handshake links, saved Handshake HTML reports, or short follow-up link messages. Use when Vincent says add to tracker, add application, add this via tracker_mcp, add this to tracekr_mcp, bulk add, or gives a job posting and expects the tracker to be updated directly.
---

# Tracker MCP Application Adds

Use this skill only for application-row adds and application-row link/status/date patches in Tracker MCP.

## Goal

Turn pasted job postings, public Handshake links, saved HTML exports, and short follow-up link messages into clean Tracker MCP application rows.

Do not drift into contacts, interactions, or broad recruiting summaries unless Vincent explicitly asks.

## Source of truth

- Tracker MCP is the source of truth for applications.
- In a new chat, when Vincent says `add`, `add to tracker`, `tracker_mcp`, or pastes a job posting in this workflow, use the Tracker MCP application tools directly rather than proposing a plan.
- Use `tracker_add_application` first for new application rows.
- Use `tracker_update_application` for later patches to an existing row.
- Application notes are user-owned. Do not create, edit, clear, or overwrite `notes` unless Vincent explicitly asks.

## Core defaults

- Default status is `applying`.
- Use `submitted` only if Vincent or the pasted posting explicitly says he already applied, for example `Applied on May 10, 2026`.
- Dates written to the sheet must use `M/D/YYYY` text format, for example `5/10/2026`; do not use ISO dates or Google Sheets serial numbers.
- Prefer canonical Handshake URLs when available.
- Pretrim every link before adding or patching: strip leading/trailing whitespace, remove fragments, remove tracking query parameters, and prefer the stable canonical job URL. Keep only meaningful query parameters if they are required for the application link to work.
- Do not create duplicates. `tracker_add_application` should be the first add path because it deduplicates by cleaned link / Handshake job ID.

## Required fields for a new application

Collect when available:
- `company`
- `role`
- `status`
- `link`
- `date_applied`
- `due_date`

Do not pass `notes` by default.

## Add workflow

1. Parse the posting or link.
2. Infer company, role, due date, status, and link. Convert dates to `M/D/YYYY` before writing.
3. Pretrim the link before writing:
   - remove leading/trailing whitespace
   - remove fragments like `#...`
   - remove tracking query params such as `utm_source`, `utm_medium`, `utm_campaign`, `trk`, `refId`, and similar noise
   - keep required job identifiers such as `ashby_jid`, Greenhouse/Lever IDs, Workday requisition IDs, LinkedIn job IDs, and Handshake job IDs
4. If a Handshake link is missing or stale, use the `handshake-tracker-links` skill workflow:
   - prefer Vincent's given HTML path
   - otherwise use the newest `/Users/vincentc9002/Desktop/jobs/Handshake Jobs*.html`
   - extract the canonical URL before adding or patching
5. Use `tracker_add_application` for the new row.
6. Confirm in one or two lines only.

## Patch workflow

Use `tracker_update_application` when:
- Vincent sends only a better link after the row already exists
- Vincent sends a public Handshake share URL plus a short company hint
- status changes from `applying` to `submitted`
- a due date or applied date needs correction

Patch only the fields that changed. Use `M/D/YYYY` for date patches and pretrim link patches before writing.

## MCP write-format guard

The tracker server has been patched so application links should write as raw visible URLs and dates should write as `M/D/YYYY`. If a future chat observes that `tracker_add_application` or `tracker_update_application` still writes `Open Link`, ISO dates, or Google Sheets serial dates, assume the running MCP process is stale. Stop using the stale MCP write path for that batch and use the same Google Sheets credentials behind Tracker MCP to write raw values directly, then tell Vincent the MCP process needs a restart/reload.

Do not keep adding rows in a broken display format after the first bad row appears.

## Deadline rule

If the posting has both:
- a Handshake apply-by date, and
- a stricter instructions deadline inside the description,

use the earlier stricter date for `due_date`.

## Handshake link rules

Preferred canonical formats:
- `https://app.joinhandshake.com/stu/jobs/<jobId>`
- `https://app.joinhandshake.com/jobs/<jobId>`
- a public share URL only if that is the only available stable URL; trim query strings/fragments first unless they are required

If Vincent gives a public share URL later, patch the existing row rather than adding a second row.

## Bulk-add rule

If Vincent is still pasting jobs and indicates more are coming, hold them and wait.

Signals include messages like:
- `prepare for a bulk add`
- `hold this`
- `just wait`
- `i'll tell u when it's time to add`

When Vincent later says `add`, add only the accumulated pending jobs that are not already in the tracker.

## Deleted-row rule

If a job was intentionally removed from tracker state, do not re-add it just because it appears in a search result or pasted HTML. Deleted means suppressed unless Vincent explicitly overrides that decision.

Canonical local tracker-state reference:
- `/Users/vincentc9002/Documents/Codex/recruiting-tracker-state/tracker-application-state.json`

## Short follow-up link messages

If Vincent sends only:
- a Handshake URL and
- a short hint like `avdi`, `oribal`, or similar,

map it to the most likely recent application row and patch only the `link` field.

## Error handling

If Tracker MCP auth fails:
- do not keep retrying blindly
- report the auth failure clearly
- if needed, point to the local tracker server path:
  `/Users/vincentc9002/Documents/Claude/Projects/tracker_mcp/server.py`

## Response style

- Be brief.
- Do the add or patch directly when enough information is present.
- Do not ask unnecessary follow-up questions.
- Do not mention Notion.
