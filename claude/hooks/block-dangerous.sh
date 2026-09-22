#!/bin/bash
# PreToolUse hook, matcher: Bash
# Blocks a short list of commands that are almost never what you meant to
# run unattended. Patterns are anchored so routine commands that merely
# *contain* a dangerous substring (e.g. `rm -rf ./dist`, `grep "DROP TABLE"`,
# `git push --force-with-lease`) still pass. Add your own patterns (prod
# deploy, DB migration tool) as you find things you never want run without a
# second look.
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')

deny() {
  local reason="$1"
  jq -nc --arg reason "$reason" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$reason}}'
  exit 0
}

[[ -z "$cmd" ]] && { echo "{}"; exit 0; }

# recursive delete of root/home/cwd itself (not scoped paths like ./dist)
if [[ "$cmd" =~ (^|[[:space:];|&])rm[[:space:]]+-rf[[:space:]]+(/|~|\.)([[:space:]]|$) ]]; then
  deny "Blocked: recursive delete of a root/home/cwd path. Re-run manually if this is really what you want."
fi

# force-push to main/master (force-with-lease is deliberately not blocked)
if [[ "$cmd" =~ (^|[[:space:];|&])git[[:space:]]+push[[:space:]]+(-f|--force)([[:space:]]+[^[:space:]]+)*[[:space:]]+(main|master)([[:space:]]|$) ]]; then
  deny "Blocked: force-push to main/master. Use a feature branch or confirm explicitly."
fi

# git reset --hard discards uncommitted work
if [[ "$cmd" =~ (^|[[:space:];|&])git[[:space:]]+reset[[:space:]]+--hard ]]; then
  deny "Blocked: git reset --hard discards uncommitted work. Stash first, or confirm explicitly."
fi

# destructive SQL: block DROP/TRUNCATE issued through a database client
# (the quoted form `sqlite3 db "DROP TABLE x"`), or appearing as a leading
# statement (start of command, after `;`, or after a newline in heredocs).
# Merely containing the words inside grep/echo strings is not blocked.
re_db_client='(^|[[:space:];|&])(sqlite3|psql|mysql|mariadb|sqlcmd)([[:space:]]|$)'
re_drop='DROP[[:space:]]+(TABLE|DATABASE)'
re_truncate='TRUNCATE[[:space:]]+'
re_lead_drop='(^|[[:space:];])DROP[[:space:]]+(TABLE|DATABASE)'
re_lead_truncate='(^|[[:space:];])TRUNCATE[[:space:]]+'
if { [[ "$cmd" =~ $re_db_client ]] && { [[ "$cmd" =~ $re_drop ]] || [[ "$cmd" =~ $re_truncate ]]; }; } \
   || [[ "$cmd" =~ $re_lead_drop ]] || [[ "$cmd" =~ $re_lead_truncate ]]; then
  deny "Blocked: destructive SQL statement. Confirm explicitly before running this."
fi

# disk-clobbering redirects (regexes kept in variables: a bare `>` inside
# an inline [[ =~ ]] regex is parsed as a redirection operator)
re_colon_truncate='(^|[[:space:];|&]):[[:space:]]*>[[:space:]]*[^[:space:]]'
re_dev_redirect='>[[:space:]]*/dev/sd[a-z]'
if [[ "$cmd" =~ $re_colon_truncate ]] || [[ "$cmd" =~ $re_dev_redirect ]]; then
  deny "Blocked: looks like a disk-clobbering redirect."
fi

echo "{}"
