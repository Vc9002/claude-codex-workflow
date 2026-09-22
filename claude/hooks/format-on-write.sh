#!/bin/bash
# PostToolUse hook, matcher: Edit|Write|MultiEdit
# Auto-formats the file Claude just touched using whichever formatter is
# installed for that file type. Silently no-ops when none is available.
# For Python, prefers the project's own venv ruff (found by walking up from
# the file) so it honors the repo's [tool.ruff] config; falls back to a PATH
# ruff. Files under ~/.claude are never touched (memory, plans, logs).
input=$(cat)
file=$(echo "$input" | jq -r '.tool_input.file_path // empty')

[[ -z "$file" || ! -f "$file" ]] && exit 0

# Never reformat Claude Code's own state.
case "$file" in
  "$HOME"/.claude|"$HOME"/.claude/*) exit 0 ;;
esac

find_ruff() {
  local dir="$1" ruff_bin=""
  while [[ "$dir" != "/" && -n "$dir" ]]; do
    if [[ -x "$dir/.venv/bin/ruff" ]]; then ruff_bin="$dir/.venv/bin/ruff"; break; fi
    dir=$(dirname "$dir")
  done
  [[ -z "$ruff_bin" ]] && command -v ruff >/dev/null 2>&1 && ruff_bin=$(command -v ruff)
  echo "$ruff_bin"
}

case "$file" in
  *.py)
    ruff_bin=$(find_ruff "$(dirname "$file")")
    [[ -n "$ruff_bin" ]] && "$ruff_bin" format "$file" >/dev/null 2>&1
    ;;
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css|*.scss)
    command -v prettier >/dev/null 2>&1 && prettier --write "$file" >/dev/null 2>&1
    ;;
  *.go)
    command -v gofmt >/dev/null 2>&1 && gofmt -w "$file" >/dev/null 2>&1
    ;;
  *.rs)
    command -v rustfmt >/dev/null 2>&1 && rustfmt "$file" >/dev/null 2>&1
    ;;
esac

exit 0
