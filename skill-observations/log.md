# Skill Observation Log

Observations captured during task-oriented work.

**Status key:** OPEN = not yet actioned | ACTIONED (YYYY-MM-DD) = skill updated/created | DECLINED (YYYY-MM-DD) = user decided not to pursue — resolved statuses always carry their resolution date

---

## 2026-09-29

### Observation 1: Cross-platform skill links must be validated as directories

**Status:** OPEN
**Date:** 2026-09-29
**Session context:** Repairing a mandatory task-observer skill that Codex could not discover on Windows.
**Skill:** task-observer
**Type:** open-source
**Phase/Area:** Activation and installation

**Issue:** A repository-tracked absolute symlink to a skill directory was checked out as a plain text file on Windows. The activation instruction remained present, but the runtime could not find a SKILL.md under the expected directory.

**Suggested improvement:** In activation setup guidance, require a post-install discovery check that the skill path is a directory containing a readable SKILL.md. Portable distributions should use copied bundles, relative links only where the platform preserves them, or an installer that creates platform-native directory links.

**Principle:** Configuration that names a mandatory capability must verify the capability's runtime discoverability on every supported platform; the presence of a path entry alone is insufficient.
