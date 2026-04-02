# Execution Reality Packet 09 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `09`
Status: `defined`

## Purpose

Packet 08 established that latest execution drag is explicit at run level.

Packet 09 now fixes the next narrow question:

```text
latest execution leakage is visible per symbol, without losing consistency with the latest run-level drag totals
```

## Invariant

Invariant 9:

```text
per-symbol execution leakage attribution is explicit for the latest run
```

## What This Checks

The packet should verify that:

- `/execution/quality/symbol-leakage/latest` returns:
  - latest `run_id`
  - latest `mode`
  - per-symbol rows with:
    - `symbol`
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
- symbol rows remain tied to the latest run only
- total attribution remains coherent:
  - symbol `notional_share` sums to `1.0`
  - symbol `execution_drag_usd` sums to latest run `execution_drag_usd`

## Why This Comes Next

Once run-level drag is visible, the next operator question is where the leakage sits.

This packet creates a first explicit symbol-level view before any stronger per-route or per-strategy attribution.

## Non-Goals

This packet does not yet prove:

- exact causal attribution for each symbol
- market-calibrated drag decomposition
- route-aware optimal execution

It only proves that the latest run has a coherent symbol-level leakage surface.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_symbol_leakage.py`

## Likely Next Packet

After this packet, the next natural direction is:

- per-route execution leakage attribution
