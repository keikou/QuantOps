# Execution Reality Packet 08 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `08`
Status: `defined`

## Purpose

Packet 07 established that latest execution quality and latest portfolio pnl can be read together.

Packet 08 now fixes the next narrow question:

```text
latest execution drag breakdown is explicit by run, and drag components remain readable without reopening raw shadow pnl rows
```

## Invariant

Invariant 8:

```text
execution drag decomposition is explicit for the latest run
```

## What This Checks

The packet should verify that:

- `/execution/quality/drag-breakdown/latest` returns:
  - latest drag `run_id`
  - latest execution `mode`
  - drag fields:
    - `gross_alpha_pnl_usd`
    - `net_shadow_pnl_usd`
    - `execution_drag_usd`
    - `slippage_drag_usd`
    - `fee_drag_usd`
    - `latency_drag_usd`
    - `component_sum_usd`
- the linkage block explicitly states:
  - `quality_run_id`
  - `drag_run_id`
  - `run_id_match`
- arithmetic remains internally coherent:
  - `component_sum_usd = slippage_drag_usd + fee_drag_usd + latency_drag_usd`
  - `execution_drag_usd = gross_alpha_pnl_usd - net_shadow_pnl_usd`

## Why This Comes Next

Once execution quality and pnl are linked, the next useful operator question is what portion of pnl leakage is explicitly attributed to execution drag components.

This packet creates that summary surface before any deeper attribution by symbol or route.

## Non-Goals

This packet does not yet prove:

- per-symbol drag attribution
- per-route economic optimality
- that the drag model is market-calibrated

It only proves that the latest run has an explicit drag decomposition surface.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_drag_breakdown.py`

## Likely Next Packet

After this packet, the next natural direction is:

- per-symbol execution leakage attribution
