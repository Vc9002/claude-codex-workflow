# Claude Source Map

Use this reference when deciding where to search.

## Durable Local Locations

- `~/Documents/Claude/Projects/SESSION_NOTES.md`: human-authored cross-session notes and setup history.
- `~/Documents/Claude/Projects/`: project documents, MCP server source folders, course folders, PDFs, DOCX, EPUBs, and prior artifacts.
- `~/Library/Application Support/Claude/local-agent-mode-sessions/`: Claude Desktop local-agent session bundles.
- `~/Library/Application Support/Claude/claude-code-sessions/`: Claude Code session metadata.
- `~/.claude/projects/`: Claude Code JSONL transcripts.
- `~/Library/Application Support/Claude/Claude Extensions/`: installed Claude Desktop extension bundles.
- `~/Library/Application Support/Claude/Claude Extensions Settings/`: enabled/disabled Claude Desktop extension settings.

## Session Bundle Shape

Claude Desktop local-agent sessions commonly store:

- `local_<uuid>.json`: metadata with title, timestamps, cwd, model, initial message, and session id.
- `local_<uuid>/audit.jsonl`: lower-level audit stream.
- `local_<uuid>/.claude/projects/*/*.jsonl`: visible Claude-style transcript if present.
- `local_<uuid>/uploads/`: user-uploaded documents and images.
- `local_<uuid>/outputs/`: generated files and exported artifacts.

Some metadata `cwd` values point inside the session `outputs/` folder. Check the sidecar folder even when `cwd` looks like outputs.

## Safety

Read Claude-owned stores in place. Do not edit, normalize, migrate, or delete them unless Vincent explicitly asks for that exact operation.
