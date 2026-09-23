# Setting up on a new machine

## 1. Prerequisites

- [Claude Code](https://claude.com/claude-code) installed (`claude` on PATH)
- [Codex CLI](https://github.com/openai/codex) installed (`codex` on PATH), if you use it
- `git`, `node` (hooks in `claude/hooks/` are a mix of `.sh` and `.js`)
- `gh` CLI logged in, if you want the same GitHub-related permissions

## 2. Clone and run the installer

```bash
git clone https://github.com/Vc9002/claude-codex-workflow.git
cd claude-codex-workflow
./install.sh
```

This symlinks (not copies) the repo's `claude/{skills,agents,commands,hooks,CLAUDE.md}`
into `~/.claude/`, and `codex/{skills,AGENTS.md}` into `~/.codex/`, so future edits
made through Claude/Codex on this new machine can be committed straight back to the
repo (`cd claude-codex-workflow && git status`). Existing files are backed up, not
deleted.

## 3. Things that need manual attention (not auto-applied, on purpose)

These are either machine-specific or would overwrite local state:

- **`claude/settings.json.example`** — only copied to `~/.claude/settings.json` if
  that file doesn't already exist. It references two optional personal tools:
  - `agent-deck` (hook handler for notifications/permission prompts) — skip those
    hook entries if you don't use it.
  - `/Users/vincentc9002/claude-selfmem/hooks/*.sh` (session memory) — update the
    path or remove those two `SessionStart`/`SessionEnd` entries if you don't have
    this repo checked out.
  - `ANTHROPIC_BASE_URL` points at a local gateway (`127.0.0.1:8787`) — remove that
    env var unless you're running the same local router.
- **`codex/config.toml.example`** — full reference of a working config, but full of
  machine-specific absolute paths (ChatGPT.app locations, local plugin marketplaces
  pointing at `$HOME`). Merge the parts you want into `~/.codex/config.toml` by hand
  rather than copying it wholesale.
- **`claude/plugins/installed_plugins.json`** — reference list of what's installed
  here. `install.sh` already runs the equivalent `claude plugin marketplace add` /
  `claude plugin install` commands for the official plugins and Headroom marketplace.
- **MCP servers, OAuth, API keys** — none of this is in the repo. Re-authenticate
  MCP servers (Gmail, Notion, Todoist, etc.) and re-add any API keys locally.
- **GSD core** (`gsd-core/`, `.gsd-*` files) — this is a plugin-managed installation
  tracked separately; run its own updater/installer rather than syncing it here.

## 4. Verify

```bash
claude doctor       # sanity-check the Claude Code install
codex --version      # if using Codex
ls ~/.claude/skills  # should list this repo's claude/skills contents
```

## 5. Keeping both machines in sync going forward

Because `install.sh` uses symlinks, edits to skills/agents/commands/hooks made in
Claude Code or Codex sessions on this machine live directly in the repo checkout.
Commit and push from `claude-codex-workflow/` as normal; `git pull` on the other
machine picks the changes up immediately (no reinstall needed).
