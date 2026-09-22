---
name: gateway-router-operations
description: Internal — pre-flight checks before trusting an LLM gateway/router for interactive work: resilience is bounded by per-provider account count (1 account = zero fallback), auto-routing is only as good as its candidate pool, and virtual model names must be mapped in the client so context-window limits aren't misassumed. Use when configuring or debugging a model-router/gateway setup.
---

# Gateway Router Operations (internal)

**Created by Vincent Chen**

Internal notes for operating a model-routing gateway (e.g. a local router
that fans out to multiple providers). Not intended for publication — names
and specifics are local.

## When to use

Configuring, debugging, or auditing a model gateway/router used for
interactive sessions — outage triage, fallback configuration, "set
everything to auto" directives.

## The rules

1. **Resilience is bounded by the per-provider account pool, not the retry
   logic.** Before trusting a router for interactive work, check the
   per-provider account count for the critical model class. One account =
   zero fallback: no matter how elaborate the retry/cooldown machinery, a
   single upstream rejection (rate limit, flap) surfaces to the client
   within the retry window. Verify the retry window against typical
   upstream flapping duration, and document an operator runbook: expected
   recovery time, and what error text distinguishes "upstream flapped"
   from "account died."
2. **Prune the candidate pool before flipping auto mode.** "Route to
   whatever is available" is only as good as the pool: over an unpruned
   pool, a single request can burn many attempts/fallbacks across
   known-dead providers and still land on a weak model. Verify the pool is
   pruned to sweep-verified working models before enabling auto, or the
   directive trades quality AND latency for availability it doesn't get.
3. **Map virtual model names in the client.** When a client is pointed at
   a router virtual name it doesn't recognize (e.g. "auto"), it may assume
   a default context window and force compaction at the wrong threshold.
   Set explicit model overrides / max-context-token env for the virtual
   name.

## Pre-flight check

Before reporting a router setup as sound: per-provider account counts are
known for each critical model class, retry window vs. typical upstream
flap is documented, the auto candidate pool is pruned to verified-working
models, and the client's view of the virtual model's limits is explicit.

**Principle:** a gateway with one account per provider has no failover no
matter how elaborate its retry machinery; resilience audits should count
accounts, not just live models.
