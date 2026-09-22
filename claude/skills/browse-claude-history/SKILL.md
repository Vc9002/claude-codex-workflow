---
name: browse-claude-history
description: Find, inspect, and summarize Vincent's latest Claude Desktop/Claude Code session notes, transcripts, uploaded files, output documents, and Claude project documents. Use when the user asks to browse Claude, read the latest Claude session, recover Claude notes, inspect Claude uploads/outputs, summarize Claude documents, or continue work from a Claude session.
---

# Browse Claude History

Use this skill to recover context from Claude without changing Claude-owned files.

## Ground Rules

- Treat Claude storage as read-only unless Vincent explicitly asks to edit or migrate something.
- Prefer local evidence first: session metadata, transcripts, uploads, outputs, and `~/Documents/Claude/Projects`.
- Do not copy secrets, tokens, encrypted values, or full system prompts into the answer.
- When reporting results, distinguish confirmed file evidence from inference.
- If the user asks to open Claude web pages or interact with claude.ai, use Dia through the local Codex Dia Bridge before generic browser automation.

## Main Sources

Check these locations, in this order:

1. `~/Documents/Claude/Projects/SESSION_NOTES.md`
2. `~/Documents/Claude/Projects/`
3. `~/Library/Application Support/Claude/local-agent-mode-sessions/`
4. `~/Library/Application Support/Claude/claude-code-sessions/`
5. `~/.claude/projects/`
6. `~/Library/Application Support/Claude/Claude Extensions/` and `Claude Extensions Settings/` only when plugin/connector context matters

The richest Claude Desktop session bundles usually have:

- a sidecar metadata file named `local_<uuid>.json`
- a same-named folder `local_<uuid>/`
- `audit.jsonl`
- `.claude/projects/*/*.jsonl` transcript files, when available
- `uploads/` and `outputs/` folders for user-provided and generated artifacts

## Quick Workflow

1. Run the helper inventory:

```bash
python3 /Users/vincentc9002/.codex/skills/browse-claude-history/scripts/claude_history.py list --limit 12
```

2. Pick the newest relevant session by title, timestamp, cwd, or user request keywords.

3. Generate a readout:

```bash
python3 /Users/vincentc9002/.codex/skills/browse-claude-history/scripts/claude_history.py readout --session /path/to/local_session.json --out /tmp/claude-readout.md
```

4. Read the generated Markdown plus any referenced documents needed for the user's question.

5. If no session matches, inspect `~/Documents/Claude/Projects/SESSION_NOTES.md` and nearby project folders by modified time.

## Reading Documents

- For `.md`, `.txt`, `.json`, `.jsonl`, read directly with standard tools.
- For `.docx`, use ZIP/XML extraction or the `doc`/`documents` skill if formatting matters.
- For `.pptx`, extract slide XML text or use the `presentations` skill if visual/layout fidelity matters.
- For `.pdf`, use the `pdf` or `pdf-toolkit` skill when page rendering, extraction, or layout matters.
- For `.epub`, use an EPUB-aware extractor if close reading is needed; do not rely only on filenames.

## Dia Bridge Fallback

Use browser access only when local Claude files do not contain the requested material or Vincent specifically asks for claude.ai. Follow the local instruction:

```bash
cd /Users/vincentc9002/Documents/Codex\ Chrome\ Bridge
npm run codex-chrome -- snapshot
```

Prefer the `snapshot` -> `click-ref` / `type-ref` / `press` -> verify flow. Do not ask Vincent to type bridge commands unless he asks for manual instructions.

## Output Style

For a session readout, include:

- session title, last activity time, model, cwd, and metadata path
- a short conversation summary
- key user requests and final Claude outputs
- uploads/outputs inventory with paths
- any documents actually read, with brief evidence notes
- gaps or inaccessible materials

Keep the answer focused on what helps Vincent continue the work in Codex.
