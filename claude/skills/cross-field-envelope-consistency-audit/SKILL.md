---
name: cross-field-envelope-consistency-audit
description: Bug-finding technique for well-audited code with no failing tests — enumerate every field of the same real-world type in one API response and diff how each is parsed; a field handled by a silently-defaulting helper while its siblings use a strict one is a high-signal hiding spot. Use when tests pass and conventional bug-hunting turns up nothing.
---

# Cross-Field Envelope Consistency Audit

**Created by Vincent Chen**

One technique for finding bugs in a codebase with heavy existing test
coverage and audit history, where "just rerun the tests" turns up nothing:
audit for *asymmetric treatment of same-shaped data* within one
response/function.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Auditing a data-normalization layer that pulls multiple fields of the same
real-world type (all USD amounts, all timestamps, all IDs) from one API
response — especially when nothing crashes and no test fails, yet a feature
is quietly broken or dark.

## The rule

Enumerate every field of a given type in the response, and diff how each
one is parsed. The outlier is the finding: e.g. 8 of 9 USD fields parsed
with a dict-aware helper (`{"value": ..., "currency": ...}`), and the
account-balance fields parsed with a plain-scalar helper that **silently
returns a default (None/0) on a shape mismatch instead of raising**. That
helper never crashes a test — it returns a plausible-looking empty value,
so the whole feature quietly goes dark on live data.

Why this catches things tests can't: the fixture was likely written by
copying the same (buggy) production assumption rather than a real captured
API response, so both sides are wrong the same way. A silent-default-on-
type-mismatch helper is the exact pattern that lets one inconsistent field
hide indefinitely — it has zero test coverage on either side, and
conventional greps for TODOs/bugs won't surface it.

**Procedure:**
1. Pick one response/function, list every field sharing a real-world type.
2. Record which helper/convention parses each.
3. Flag any field whose helper silently defaults (returns None/0/empty)
   instead of raising — then check what consumes that field downstream
   (sizing, display, gating) and what a None there does to it.
4. Treat a helper that can't distinguish "absent" from "unexpected shape"
   as itself the bug class to report.

## Pre-flight check

Before reporting a finding: the field enumeration is exhaustive for the
type (not a sample), the outlier's helper behavior on a shape mismatch was
verified by reading the helper, and the downstream consumer's behavior on
the default value was traced, not assumed.

**Principle:** fields that share a real-world type but are parsed by
different helpers are a high-signal place to find bugs that both production
code and its own test fixtures independently got wrong the same way.
