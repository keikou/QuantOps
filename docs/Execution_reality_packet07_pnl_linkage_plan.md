# Execution Reality Packet 07 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `07`
Status: `defined`

## Purpose

Packet 06 established that latency evidence is explicit by mode and execution route.

Packet 07 now fixes the next narrow question:

```text
latest execution quality and latest portfolio pnl evidence can be read together as one explicit linkage surface
```

## Invariant

Invariant 7:

```text
execution quality to portfolio pnl linkage is explicit for the latest run
```

## What This Checks

The packet should verify that:

- `/execution/quality/pnl-linkage/latest` returns:
  - latest execution `run_id`
  - latest execution `cycle_id`
  - latest execution `mode`
  - execution quality fields:
    - `order_count`
    - `fill_count`
    - `fill_rate`
    - `avg_slippage_bps`
    - `latency_ms_p50`
    - `latency_ms_p95`
  - portfolio pnl fields:
    - `portfolio_run_id`
    - `total_equity`
    - `realized_pnl`
    - `unrealized_pnl`
    - `gross_pnl`
    - `fees_paid`
    - `net_pnl_after_fees`
    - `drawdown`
- the linkage block explicitly states whether execution `run_id` matches the portfolio snapshot `run_id`

Explicit linkage statement:

```text
run_id matches the portfolio snapshot run_id
```
- pnl arithmetic remains internally coherent:
  - `gross_pnl = realized_pnl + unrealized_pnl`
  - `net_pnl_after_fees = gross_pnl - fees_paid`

## Why This Comes Next

After visibility for slippage and latency, the next practical question is whether operators can read execution quality and pnl consequence on the same surface without manually joining multiple endpoints.

This packet creates that explicit bridge before any stronger economic attribution work.

## Non-Goals

This packet does not yet prove:

- causal pnl attribution by route
- a precise slippage-to-pnl cost model
- economic optimality of the execution path

It only proves that execution quality and portfolio pnl are surfaced together with explicit run linkage.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_pnl_linkage.py`

## Likely Next Packet

After this packet, the next natural direction is:

- execution drag decomposition by run
