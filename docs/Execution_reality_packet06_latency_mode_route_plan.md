# Execution Reality Packet 06 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `06`
Status: `defined`

## Purpose

Packet 05 established that latest slippage summary is separated by mode and retains route attribution.

Packet 06 now fixes the next narrow question:

```text
latency evidence remains explicit by mode and execution route for the latest run in each mode
```

## Invariant

Invariant 6:

```text
execution latency summary is explicit by mode and execution route
```

## What This Checks

The packet should verify that:

- `/execution/quality/latency-by-mode-route` returns rows keyed by latest `mode` and `route`
- each row preserves:
  - `run_id`
  - `cycle_id`
  - `mode`
  - `route`
  - `fill_count`
  - `avg_latency_ms`
  - `latency_ms_p50`
  - `latency_ms_p95`
- latency evidence from different routes remains separated within the same mode
- latency evidence from different modes does not collapse into one route row
- each row remains internally coherent:
  - `fill_count > 0`
  - latency fields are non-negative
  - `latency_ms_p95 >= latency_ms_p50`

## Why This Comes Next

Once slippage is mode-separated, the next useful realism question is whether execution path latency is still visible at a comparable grain.

That comparison needs:

- latest run per mode
- route attribution from the execution plan
- fill latency evidence aggregated without cross-mode bleed

## Non-Goals

This packet does not yet prove:

- that any route is economically optimal
- that latency is venue-realistic
- that live-mode latency is production-calibrated

It only proves that the repo preserves mode/path latency evidence in a stable operator-facing summary surface.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_latency_mode_route.py`

## Likely Next Packet

After this packet, the next natural direction is:

- execution-quality to pnl leakage linkage
