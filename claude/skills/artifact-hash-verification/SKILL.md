---
name: artifact-hash-verification
description: Internal — verify embedded artifact_hash fields in this repo's config/models/ JSON artifacts across serialization conventions, and triage files that don't self-verify. Use when auditing model-artifact integrity or building verification tooling.
---

# Artifact Hash Verification (internal)

Verifies embedded `artifact_hash` fields in `config/models/` JSON model
artifacts. Internal skill: contains this repo's specific conventions.

## The convention grid

Recompute the hash as sha256 of `json.dumps(payload_without_artifact_hash,
sort_keys=True)` over a 2×2 grid of serializers before declaring a
MISMATCH: separators `(",", ":")` (compact) vs default `(", ", ": ")`,
each with `ensure_ascii=False` vs `True`. Then try `sort_keys=False` and
raw-text variants.

- Production and archived artifacts (regression models, esports v3–v6,
  measured-edge, kbo/npb, market-residual, ablation) verify with
  **compact separators + ensure_ascii=False**.
- The 2026-08-11 challenger rebuilds (nfl/wnba/tennis rebuild) verify with
  **default separators + ensure_ascii=True** — a compact-only checker
  reports false MISMATCHes on these.
- Calibrator files carry `calibrator_hash`/`base_model_hash` instead of
  `artifact_hash` — no recomputation standard applies to them.

## Expected non-verifiers

- `archive/wnba-spread-baseline-v1.json` — `_retired` fields were appended
  after hashing; expected, not corruption.
- `challengers/mlb-two-head-v1.json`, `mlb-two-head-real-features-v1.json`,
  `soccer-poisson-dc-rebuild-v1.json` — stale hashes (content edited
  post-generation); treat as findings to re-hash, not proof of tampering,
  until git history shows otherwise.

## Pre-flight

Before reporting any hash result:

- Run the full grid — a MISMATCH under one convention is not a mismatch.
- For a genuine non-verifier, check git history for post-generation edits
  before calling it corruption.
</content>
