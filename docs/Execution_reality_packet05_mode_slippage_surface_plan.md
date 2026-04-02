# Execution Reality Packet 05 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `05`
Status: `defined`

## Purpose

Packet 04 established that the latest execution quality surfaces stay run-scoped and mode-consistent.

Packet 05 now fixes the next narrow question:

```text
slippage summary remains explicitly separated by mode, with route attribution preserved for the latest run in each mode
```

## Invariant

Invariant 5:

```text
execution quality by-mode summary is explicit, mode-separated, and route-attributable
```

## What This Checks

The packet should verify that:

- `/execution/quality/by-mode` returns one latest summary row per mode
- each row preserves:
  - `run_id`
  - `cycle_id`
  - `mode`
  - `order_count`
  - `fill_count`
  - `fill_rate`
  - `avg_slippage_bps`
  - `latency_ms_p50`
  - `latency_ms_p95`
- each mode row retains a non-empty `route_mix` derived from the latest run in that mode
- paper and shadow mode rows do not collapse into one another
- distinct slippage levels remain visible as distinct mode-level evidence

## Why This Comes Next

Before proving stronger economic realism by venue or execution path, the repo first needs a stable comparison surface showing:

- latest execution quality per mode
- latest slippage per mode
- route attribution for the run that produced that mode's latest evidence

## Non-Goals

This packet does not yet prove:

- that paper/live/shadow slippage is economically calibrated
- that route-level costs are production-realistic
- that venue selection is optimal

It only proves that the current repo can expose mode-separated slippage evidence without losing route attribution.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_mode_slippage_surface.py`

## Likely Next Packet

After this packet, the next natural direction is:

- latency realism by mode or execution path
