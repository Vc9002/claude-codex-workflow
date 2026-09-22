---
name: macos-battery-drain-diagnosis
description: Diagnose macOS battery drain, energy consumption, and background process activity. Reconstruct historical power timelines, use differential interval snapshots, validate active power/sleep policies, and execute time-bounded log queries. Use when investigating battery loss, unexpected idle drain, or high-energy processes on macOS.
---

# macOS Battery Drain & Energy Diagnosis

**Created by Vincent Chen**

A methodology for diagnosing macOS battery loss, isolating background power
consumers, and verifying power-management policies without contaminating
measurements.

**Licence:** This skill is released under CC BY 4.0 — share and adapt for
any purpose with credit.

**Feedback & Support:** Not yet published to a public repository — route
methodology feedback, or cases where the agent didn't follow these rules,
directly to the author.

## When to use

Investigating unexpected macOS battery drops, idle battery drain during sleep/clamshell
mode, high-energy background processes, or evaluating power management configurations.

## Rule 1 — reconstruct the timeline before attributing drain to a process

A point-in-time snapshot of high CPU or energy consumption does not prove historical
causation. The claimed battery drop may not have occurred during the suspected window
(e.g. 80% optimized battery charging hold points or estimator jumps vs. real discharge).

**Diagnostic sequence:**
1. Reconstruct charge percentages, power source transitions (AC vs. Battery), and
   sleep/wake cycles from system power logs (`pmset -g log`).
2. Verify that energy was genuinely lost during the claimed window before naming
   a culprit process.
3. Distinguish between actual discharge, charging caps (80% hold), and fuel-gauge
   recalibrations.

## Rule 2 — isolate interval load using differential snapshots

Live instantaneous CPU/energy metrics are noisy and easily misleading. Short-window
attribution requires comparing cumulative counters across a bounded interval.

**To isolate drain culprits over an observation interval:**
1. **Initial snapshot:** Capture timestamped raw capacity (mAh), voltage, cumulative
   process CPU times (`ps -eo pid,time,comm`), disk I/O, network traffic, and active
   power assertions (`pmset -g assertions`).
2. **Follow-up snapshot:** After the interval, re-capture identical metrics and compute
   exact interval deltas (change in CPU time, change in capacity).
3. **Power policy check:** Inspect both battery and AC sleep profiles (`pmset -g custom`)
   to confirm whether display/system sleep was inhibited or if power source state
   was misreported.

## Rule 3 — bound power-log queries before execution

Diagnostic tools must not become energy consumers themselves. Queries like `pmset -g log`
generate massive historical text streams; piping into downstream utilities (`tail`, `grep`)
forces the underlying generator to process full logs, consuming 100% CPU.

**Query discipline:**
1. Prefer time-bounded unified log predicates (`log show --predicate ... --start ...`).
2. If using `pmset -g log`, run with explicit timeouts or time filters where supported.
3. Verify diagnostic processes terminate immediately after execution before measuring
   system idle state again.

## Pre-flight check

Before concluding a macOS battery drain investigation:
1. Confirm the power-event timeline proves actual discharge in the target interval.
2. Attribute process energy via differential interval deltas, not single-point metrics.
3. Check active sleep assertions (`pmset -g assertions`) and power profiles (`pmset -g custom`).
4. Ensure all power diagnostics were bounded and left no lingering background processes.
