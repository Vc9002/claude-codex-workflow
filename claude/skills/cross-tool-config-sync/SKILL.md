---
name: cross-tool-config-sync
description: Share or synchronize Vincent's skills, plugin files, MCP definitions, and hooks across Claude Code, Codex, and other installed agent runners after verifying each tool's supported configuration format and scope.
---

# Cross-tool configuration sync

Internal skill for Vincent's local agent environment. Use for requested sharing
or migration across agent runners; configuration on disk and a running session
loading it are separate outcomes.

## Establish compatibility and authority

1. Inventory only the requested tools and components from live directories,
   installed CLI help, plugin manifests, and loader evidence. For each, record
   version, configuration path and scope, supported skills/MCP/hooks, expected
   schema, and reload behavior. Mark unsupported or unverified capabilities
   explicitly; do not invent equivalents.
2. Choose the canonical source per component from the user's instruction and
   current session evidence. Existing links are evidence of an earlier choice,
   not a universal rule that Claude is authoritative. Inspect real paths and
   detect link cycles, broken targets, local-only content, and versioned caches.
3. Claude skills may live under ~/.claude/skills and Codex skills under
   ~/.codex/skills; verify current discovery before using those paths. Share
   complete compatible skill bundles, preserving references, scripts, assets,
   and licenses. Plugin sharing additionally requires compatible manifests,
   loader conventions, and version/update behavior.

## Apply a targeted change

1. Freshly read both source and target immediately before mutation. Back up each
   affected file or directory and verify that the backup preserves its contents,
   permissions, and link targets. Keep a concrete rollback path.
2. Symlink only components whose format and loader semantics both tools support.
   Prefer individual compatible bundles when directory-wide replacement would
   hide target-only content. Never symlink whole configuration roots merely to
   share skills; versioned plugin targets need an explicit update strategy.
3. Translate MCP and hook entries into the target's native schema; do not link
   JSON and TOML configurations together or assume their transports, environment
   expansion, hook events, or approval behavior are interchangeable. Preserve
   unrelated settings and tool-specific security controls.
4. Parse serialized state into native structures, merge only authorized entries,
   and assert preservation of unrelated keys. Re-read for concurrent changes
   before replacement; rebase if changed. Use an atomic targeted replacement
   and retain existing restrictive permissions. Keep credentials out of argv,
   logs, and displayed diffs; use supported secret references when available and
   protect any required secret-bearing files and backups.

## Verify before reporting

Re-read these rules and verify resolved link targets, bundle completeness,
configuration parsing, preserved unrelated settings, permissions, and rollback
artifacts. Enumerate successes and gaps against the original requested component
count, rather than treating a filtered inspection as complete coverage.

Use each tool's own discovery/status mechanism and, where authorized, a minimal
runtime operation to establish actual loading. Inspect every material child exit
when using a wrapper. Distinguish disk configuration, authenticated connection,
tool discovery, and successful runtime behavior. Shared files alone do not prove
that both applications capture memory or load hooks. If a new session is needed,
report that boundary and leave runtime loading unverified until observed.

**Decision checks:** JSON MCP source plus TOML target requires a targeted schema
translation; a target without hooks gets a reported capability gap; an existing
Codex-only skill survives sharing another bundle; a successful symlink without
new-session evidence supports only an on-disk completion claim.
