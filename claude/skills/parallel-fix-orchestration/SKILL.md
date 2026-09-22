---
name: parallel-fix-orchestration
description: Orchestrate N parallel fix agents over one shared checkout — disjoint file ownership, shared-state test assignment, and a planned full-suite integration run. Use when partitioning a multi-file fix pass across concurrent agents.
---

# Parallel Fix Orchestration

**Created by Claude, distilled from the operator's real session observations.**

Coordinates several agents fixing a codebase concurrently in one shared
working tree. Originated from a real incident: four parallel fix agents
with disjoint file ownership produced no write conflicts, yet a
cross-agent semantic coupling still left a red test that only the final
integration run caught.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** If questions arise about the methodology, or the
user gives constructive feedback on output derived from this skill, route
it to the operator of the workspace where this skill is installed. (No
public repository exists yet — do not add a repository link until one
does.) If feedback stems from the agent not following the skill's rules,
acknowledge and correct.

## When to use

A fix pass over many files that the user wants done in parallel (or that
benefits from parallel review), where multiple agents will edit the same
checkout in the same session.

## The three rules

1. **Disjoint file ownership.** Give every agent an explicit allow-list of
   files it may edit. Everything else is read-only — instruct "report,
   don't edit" for shared files. File-level isolation prevents write
   conflicts — and nothing more.
2. **Assign shared-state tests up front.** Before partitioning, identify
   which tests pin shared state (the real shipped config, artifact paths,
   golden files, env-sensitive defaults) and assign each to the agent that
   owns that state. Otherwise one agent fixes a config while another pins
   a test to its old value.
3. **The full suite is part of the plan.** Cross-agent couplings are
   invisible to per-agent targeted runs. The final step is always one full
   test-suite run; any red test is routed back to its owning agent, and
   the integration-run output is what gets reported — not the sum of the
   agents' claims.
4. **Resume interrupted agents via SendMessage.** Distinguish agent failure
   modes by cause: infrastructure disruptions (e.g. host sleep, API connection
   drops, transient timeouts) do not erase the agent's internal state. Resume
   the interrupted agent using `send_message` rather than spawning a fresh agent
   that would have to reconstruct context from scratch. Instruct long-running
   agents to write durable intermediate checkpoints (disk files, stubs). Only
   unrecoverable task logic errors warrant a fresh agent spawn.

## Pre-flight

Before reporting "fixes complete":

- Re-run the FULL suite (not per-agent subsets) and capture the output.
- If red, route each failure to the owning agent before declaring done.
- Report the integration-run result verbatim, including any failures.

## Anti-patterns

- Allowing two agents to edit the same file, or "whoever gets there
  first" ownership.
- Targeted per-agent test runs presented as the integration result.
- Reporting agent-completion messages as the pass's outcome — the pass's
  outcome is one green full-suite run.

## Consolidation refactors (single source of truth)

A related but distinct task: collapsing N parallel configs/registries/code
paths that have drifted into one canonical source, rather than fixing bugs
across a fixed file set. Originated from a real incident: a config file
listed many allowed entries but the validator, health check, and server
only ever touched one of them — a "split personality" invisible until
someone read the config against the code that consumed it.

The pattern that worked, in order:

1. **Identify the keystone.** Find the one artifact (a config file plus its
   validator, a schema plus its loader) whose drift is causing the split
   personality. That's what the new module becomes the source of truth for.
2. **Build one new module, don't reimplement in parallel.** Give it
   fail-closed validation per entry (a broken secondary entry gets disabled
   with a recorded error; a broken primary entry raises) — classify this
   explicitly in the data contract, don't leave it implicit.
3. **Preserve the legacy public API via delegation, not reimplementation.**
   The old module keeps its function signatures AND its exact
   error/exception message strings if existing tests assert on them —
   internally it just calls the new module. Reimplementing the old surface
   in parallel guarantees drift between "the config," "the validator," and
   "the server" all over again.
4. **Migrate the real checked-in config in the same commit** the new module
   lands, with the legacy schema's derivation path still implemented and
   tested — so no consumer breaks mid-migration.
5. **Pin the real checked-in config as a test fixture, not just a
   `tmp_path` fixture.** The highest-value test is not unit-level: load the
   actual file that ships and assert every entry in it resolves. A
   contract requirement (e.g. "every listed entry must be valid") becomes a
   test before it becomes a CI step, and it catches drift the moment new
   entries are added.

Anti-pattern specific to this mode: adding the new source-of-truth module
alongside the old one without making the old one delegate — now there are
two places that can each be "right," and nothing forces them to agree.
