# Execution Reality Packet 10 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `10`
Status: `defined`

## Purpose

Packet 09 established that latest execution leakage is visible per symbol.

Packet 10 now fixes the next narrow question:

```text
latest execution leakage is visible per route, without losing consistency with the latest run-level drag totals
```

## Invariant

Invariant 10:

```text
per-route execution leakage attribution is explicit for the latest run
```

## What This Checks

The packet should verify that:

- `/execution/quality/route-leakage/latest` returns:
  - latest `run_id`
  - latest `mode`
  - per-route rows with:
    - `route`
    - `fill_count`
    - `gross_notional_usd`
    - `notional_share`
    - `avg_slippage_bps`
    - `avg_latency_ms`
    - `avg_fee_bps`
    - `slippage_drag_usd`
    - `fee_drag_usd`
    - `latency_drag_usd`
    - `execution_drag_usd`
- route rows remain tied to the latest run only
- total attribution remains coherent:
  - route `notional_share` sums to `1.0`
  - route `execution_drag_usd` sums to latest run `execution_drag_usd`

## Why This Comes Next

After symbol-level leakage, the next operator question is which execution path carried the leakage.

This packet creates a first route-level view before any deeper venue-aware attribution.

## Non-Goals

This packet does not yet prove:

- exact causal attribution for each route
- venue-calibrated drag decomposition
- route optimality

It only proves that the latest run has a coherent route-level leakage surface.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_route_leakage.py`

## Likely Next Packet

After this packet, the next natural direction is:

- execution reality lane status review
