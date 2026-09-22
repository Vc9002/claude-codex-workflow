---
name: promotion-request-preflight
description: Before executing any promotion/activation directive ("promote model X"), run a two-part preflight — check the candidate's own recorded evaluation against the project's gate, and trace the producer-to-consumer path to confirm a live consumer actually reads what the promotion mutates. Use when acting on promotion, activation, or rollout directives.
---

# Promotion Request Preflight

**Created by Vincent Chen**

"Promote X" is an instruction about intent, not a verified statement that
X is promotable — and not evidence that anything is wired to consume the
promotion.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Acting on any short directive to promote, activate, or roll out a model,
feature, or config — especially where the directive comes without
attached evidence.

## The rule — two-part preflight, report before executing

1. **Evidence check.** Read the candidate's OWN recorded evaluation and
   any eligibility/qualification block (its artifact, not your memory of
   it), and compare against the project's documented gate. A candidate can
   be promoted with its own artifact recording a failed holdout (CI
   entirely negative) and an explicit `eligible: false` — shipping it
   would activate a known underperformer.
2. **Wiring check.** Trace the producer-to-consumer path: confirm a live
   consumer actually reads what the promotion mutates. If the promotion
   command mutates a map that no serving path reads for the target market,
   the promotion "succeeds" and produces exactly zero predictions — a
   config change nothing consumes is indistinguishable from success until
   someone looks for the output.

Surface a conflict as a blocker with the specific numbers (CI bounds,
gate value, which consumer reads what), rather than executing or silently
declining. The directive is then either rescinded or amended with the
facts on the table.

## Pre-flight check

Before executing a promotion: the artifact's own evaluation was read and
compared against the documented gate, the consumer chain was traced end to
end and confirmed to read the mutated entry, and any conflict was surfaced
as a numbered blocker.

**Principle:** a promotion directive encodes intent, not eligibility and
not wiring; check the candidate's own recorded evidence against the gate,
and confirm the switch you are about to flip is actually read by something
downstream.
