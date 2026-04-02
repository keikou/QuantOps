# Execution Reality Packet 03 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Packet: `03`
Status: `defined`

## Purpose

Packet 02 established that partial-fill and rejection states are operator-visible.

Packet 03 now fixes the next narrow question:

```text
slippage evidence is visible on both summary and fill surfaces, and each fill remains quote-attributable
```

## Invariant

Invariant 3:

```text
latest slippage summary and latest fill evidence remain coherent and quote-attributable
```

## What This Checks

The packet should verify that:

- `/execution/quality/latest_summary` exposes `avg_slippage_bps`
- `/execution/quality/latest_summary` preserves `run_id`, `cycle_id`, and `mode`
- `/execution/fills` exposes `slippage_bps`
- `/execution/fills` preserves quote context fields:
  - `bid`
  - `ask`
  - `arrival_mid_price`
  - `price_source`
  - `quote_time`
  - `quote_age_sec`

## Why This Comes Next

Before proving deeper slippage realism, the repo first needs a stable contract showing:

- the latest summary-level slippage signal
- the fill-level quote context that explains where slippage came from

## Non-Goals

This packet does not yet prove:

- that slippage is economically realistic
- that the model is venue-realistic
- that mode-to-mode slippage differences are calibrated
- that quote quality is production-grade

It only proves that the evidence needed for that later work is already operator-visible.

## Suggested Verifier

- `test_bundle/scripts/verify_execution_reality_slippage_visibility.py`

## Likely Next Packet

After this packet, the next natural direction is:

- slippage realism by mode or execution path
