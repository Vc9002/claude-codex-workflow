# Setting up on a new machine

## 1. Prerequisites

- [Claude Desktop](https://claude.com/download) and/or [Claude Code](https://claude.com/claude-code)
- [Codex desktop app](https://chatgpt.com/codex) and/or [Codex CLI](https://github.com/openai/codex)
- `git`, `node` (hooks in `claude/hooks/` are a mix of `.sh` and `.js`)
- `gh` CLI logged in, if you want the same GitHub-related permissions

## 2. Clone and run the installer

```bash
git clone https://github.com/Vc9002/claude-codex-workflow.git
cd claude-codex-workflow
./install.sh
```

This symlinks (not copies) the repo's Claude Code and Codex shared workflow files
into their respective config folders, so future edits
made through Claude/Codex on this new machine can be committed straight back to the
repo (`cd claude-codex-workflow && git status`). Existing files are backed up, not
deleted.

## 3. Apply app settings

The command-line tools and desktop apps do not all use the same settings files:

- **Claude Code** reads `~/.claude/settings.json`; review and merge
  `claude/settings.json.example`. The installer seeds it only when no local file
  exists.
- **Claude Desktop** reads `%APPDATA%/Claude/claude_desktop_config.json` on
  Windows and `~/Library/Application Support/Claude/claude_desktop_config.json`
  on macOS. Start from `claude/desktop/claude_desktop_config.json.example` and
  merge any MCP servers you want. This machine had no Claude Desktop MCP config
  to import, so the template is intentionally empty.
- **Codex desktop and Codex CLI share `~/.codex/config.toml`**. Review and merge
  `codex/config.toml.example`; shared skills and global instructions are already
  linked by the installer.

Restart the relevant app after changing its config. Existing config files are
not overwritten by the installer.

## 4. Things that need manual attention (not auto-applied, on purpose)

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
- **MCP servers and local plugins** — add machine-specific executable paths and
  credentials to the local app config. The tracked Codex template includes only
  the portable OpenAI Developer Docs MCP entry; runtime paths, project trust, and
  credential-bearing servers stay local.
- **`claude/plugins/installed_plugins.json`** — reference list of what's installed
  here. `install.sh` already runs the equivalent `claude plugin marketplace add` /
  `claude plugin install` commands for the official plugins and Headroom marketplace.
- **OAuth, API keys, and credential-bearing MCP servers** — sign in again on each
  machine and configure credentials locally. Do not paste tokens into tracked
  config templates.
- **GSD core** (`gsd-core/`, `.gsd-*` files) — this is a plugin-managed installation
  tracked separately; run its own updater/installer rather than syncing it here.

## 5. Verify

```bash
claude doctor       # sanity-check the Claude Code install
codex --version      # if using Codex
ls ~/.claude/skills  # should list this repo's claude/skills contents
```

## 6. Keeping both machines in sync going forward

Because `install.sh` uses symlinks, edits to skills/agents/commands/hooks made in
Claude Code or Codex sessions on this machine live directly in the repo checkout.
Commit and push from `claude-codex-workflow/` as normal; `git pull` on the other
machine picks the changes up immediately (no reinstall needed).
