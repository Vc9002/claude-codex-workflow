# claude-codex-workflow

Portable workflow settings for Claude Desktop, Claude Code, the Codex desktop
app, and Codex CLI. It includes skills, instructions, hooks, plugins, and safe
configuration templates. See [SETUP.md](SETUP.md) before applying settings on a
new machine.

## Layout

```
claude/
  CLAUDE.md                  global instructions (~/.claude/CLAUDE.md)
  settings.json.example      Claude Code settings/hooks/permissions template
  desktop/
    claude_desktop_config.json.example  Claude Desktop MCP config template
  skills/                    skills (~/.claude/skills)
  agents/                    subagents (~/.claude/agents)
  commands/                  slash commands (~/.claude/commands)
  hooks/                     hook scripts (~/.claude/hooks)
  plugins/                   installed_plugins.json / known_marketplaces.json reference
codex/
  AGENTS.md                  global instructions (~/.codex/AGENTS.md)
  config.toml.example        Codex desktop + CLI preferences/MCP/plugin template
  skills/                    skills (~/.codex/skills)
install.sh                   symlinks the above into place on a new machine
SETUP.md                     step-by-step setup, including what NOT to blindly copy
```

## Quick start

```bash
git clone https://github.com/Vc9002/claude-codex-workflow.git
cd claude-codex-workflow
./install.sh
```

See [SETUP.md](SETUP.md) for prerequisites, plugin installation, and the
handful of machine-specific settings (local hook paths, MCP servers, API
keys) that are intentionally left out of automatic sync.

## What's excluded

Session history, caches, auth tokens/OAuth state, daemon logs, project trust
decisions, and machine-specific MCP commands are not tracked. Codex desktop and
CLI share `~/.codex/config.toml`; Claude Desktop has its own MCP config file.
See `SETUP.md` for which files apply to each app and how to merge them safely.
