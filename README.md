# claude-codex-workflow

Personal workflow — skills, subagents, slash commands, hooks, and global
instructions — for [Claude Code](https://claude.com/claude-code) and the
[OpenAI Codex CLI](https://github.com/openai/codex). Designed to be cloned
onto a new machine and applied with one script; see [SETUP.md](SETUP.md).

## Layout

```
claude/
  CLAUDE.md                  global instructions (~/.claude/CLAUDE.md)
  settings.json.example      settings/hooks/permissions reference (~/.claude/settings.json)
  skills/                    skills (~/.claude/skills)
  agents/                    subagents (~/.claude/agents)
  commands/                  slash commands (~/.claude/commands)
  hooks/                     hook scripts (~/.claude/hooks)
  plugins/                   installed_plugins.json / known_marketplaces.json reference
codex/
  AGENTS.md                  global instructions (~/.codex/AGENTS.md)
  config.toml.example        config reference (~/.codex/config.toml) — machine-specific, merge manually
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

Session history, caches, auth tokens/OAuth state, daemon logs, and other
machine-local runtime state are not tracked here — only the parts of the
workflow that define *behavior* (skills, agents, commands, hooks, global
instructions, plugin list).
