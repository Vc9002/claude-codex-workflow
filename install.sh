#!/usr/bin/env bash
# Installs this repo's Claude Code + Codex CLI workflow into the current machine.
# Safe to re-run. Existing files are backed up with a .bak-<timestamp> suffix.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d%H%M%S)"

backup_and_link() {
  local src="$1" dest="$2"
  if [ -e "$dest" ] && [ ! -L "$dest" ]; then
    mv "$dest" "$dest.bak-$TS"
    echo "Backed up existing $dest -> $dest.bak-$TS"
  fi
  rm -rf "$dest"
  ln -s "$src" "$dest"
  echo "Linked $dest -> $src"
}

echo "== Claude Code =="
mkdir -p "$HOME/.claude"
backup_and_link "$REPO_DIR/claude/skills"   "$HOME/.claude/skills"
backup_and_link "$REPO_DIR/claude/agents"   "$HOME/.claude/agents"
backup_and_link "$REPO_DIR/claude/commands" "$HOME/.claude/commands"
backup_and_link "$REPO_DIR/claude/hooks"    "$HOME/.claude/hooks"
backup_and_link "$REPO_DIR/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"

if [ ! -e "$HOME/.claude/settings.json" ]; then
  cp "$REPO_DIR/claude/settings.json.example" "$HOME/.claude/settings.json"
  echo "Wrote $HOME/.claude/settings.json (review it — hooks reference tools like agent-deck and claude-selfmem that are optional)."
else
  echo "$HOME/.claude/settings.json already exists — not overwriting. Compare against claude/settings.json.example manually."
fi

echo
echo "== Codex CLI =="
mkdir -p "$HOME/.codex"
backup_and_link "$REPO_DIR/codex/skills"    "$HOME/.codex/skills"
backup_and_link "$REPO_DIR/codex/AGENTS.md" "$HOME/.codex/AGENTS.md"
echo "Not linking codex/config.toml.example automatically — it's machine-specific (app paths, MCP servers). Merge manually into $HOME/.codex/config.toml."

echo
echo "== Claude Code plugins/marketplaces =="
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add anthropics/claude-plugins-official || true
  claude plugin marketplace add thedotmack/claude-mem || true
  claude plugin marketplace add chopratejas/headroom || true
  claude plugin install frontend-design@claude-plugins-official || true
  claude plugin install superpowers@claude-plugins-official || true
  claude plugin install rust-analyzer-lsp@claude-plugins-official || true
  claude plugin install claude-mem@thedotmack || true
  claude plugin install headroom@headroom-marketplace || true
else
  echo "claude CLI not found on PATH — install Claude Code first, then re-run this section:"
  echo "  see claude/plugins/installed_plugins.json for the full plugin list."
fi

echo
echo "Done. See SETUP.md for manual follow-up steps (MCP servers, API keys, GSD core)."
