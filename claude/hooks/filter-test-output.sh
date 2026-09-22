#!/bin/bash
# PreToolUse hook, matcher: Bash
# Based on Anthropic's official Claude Code docs example
# (code.claude.com/docs/en/costs), extended to also match `python -m pytest`
# and venv-pytest invocations, and to build the output JSON with jq so quoted
# arguments can't break the rewritten command.
input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')

# If running tests, filter to show only failures
if [[ "$cmd" =~ ^(npm[[:space:]]+test|go[[:space:]]+test|pytest([[:space:]]|$)) ]] \
   || [[ "$cmd" =~ (^|[[:space:];|&])(env[[:space:]]+[^;&|]*)?([^;&|[:space:]]*/)?python[0-9.]*[[:space:]]+-m[[:space:]]+pytest([[:space:]]|$) ]]; then
  filtered_cmd="$cmd 2>&1 | grep -A 5 -E '(FAIL|ERROR|error:)' | head -100"
  jq -nc --arg cmd "$filtered_cmd" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"allow",updatedInput:{command:$cmd}}}'
else
  echo "{}"
fi
