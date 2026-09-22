---
name: handshake-tracker-links
description: Extract canonical Handshake job URLs from saved Handshake Jobs HTML reports and use them for Tracker MCP application adds/updates. Use when Vincent mentions tracker_mcp, Handshake job links, saved Handshake Jobs HTML, raw URLs, or patching missing tracker links.
---

# Handshake Tracker Links

Keep Tracker MCP rows tied to exact Handshake posting URLs.

## Workflow
1. Find the HTML. Prefer Vincent's given path, then newest `/Users/vincentc9002/Desktop/jobs/Handshake Jobs*.html`, then `/Users/vincentc9002/Desktop/Handshake Jobs.html`.
2. Extract company, role, and URL before adding/updating Tracker MCP.
3. Prefer visible `Raw URL:` lines; otherwise use `initialJobs` data; otherwise use nearby `<a href>` job links.
4. Use Tracker MCP as source of truth: `tracker_add_application` for new rows, `tracker_update_application` for missing/bad links. Do not write application notes unless Vincent explicitly asks.
5. If pasted text and HTML disagree, use employer/role from the posting text but URL from the matching HTML entry; mention meaningful mismatches briefly.

## Daily Search HTML Rule
For `/Users/vincentc9002/Desktop/jobs/Handshake Jobs YYYY-MM-DD.html`, each job must expose both:

```text
Link: clickable embedded link
Raw URL: full visible Handshake URL
```

Use prior `Handshake Jobs*.html` files as duplicate sources. Do not create a separate `.txt` link file; future Codex runs extract from visible `Raw URL:` lines.

## Helper
```bash
python3 /Users/vincentc9002/.codex/skills/handshake-tracker-links/scripts/extract_handshake_links.py   "/Users/vincentc9002/Desktop/jobs/Handshake Jobs YYYY-MM-DD.html"   --company "The ABLE Firm" --role "Legal Assistant"
```

The script prints JSON; use the returned `link`. If multiple fuzzy matches appear, choose the exact company+role match first.

## Field Rules
- Status: `submitted` only when Vincent/posting says applied; otherwise `applying`.
- Dates: ISO `YYYY-MM-DD` for `date_applied` and `due_date`.
- If Handshake apply-by date conflicts with a stricter instructions deadline, use the earlier stricter date and mention it.
- Canonical URL format: `https://app.joinhandshake.com/stu/jobs/<jobId>`.
