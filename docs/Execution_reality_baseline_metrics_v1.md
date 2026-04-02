# Execution Reality Baseline Metrics v1

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `post_hardening_next_lane`
Lane: `Execution Reality`
Baseline: `v1`
Status: `defined_and_verifiable`

## Purpose

This file fixes the first baseline metric set for `Execution Reality v1`.

It does not create a new lane.

It freezes which metrics should be read from the existing verified surfaces before any further optimization work begins.

## Baseline Set

The first baseline set should lock:

1. average slippage by mode
2. average slippage by route
3. latency distribution by mode and route
4. execution drag percentage
5. top leakage symbols
6. top leakage routes

## Source Surfaces

These baseline fields should be read from the current repo surfaces:

- `/execution/quality/by-mode`
- `/execution/quality/route-leakage/latest`
- `/execution/quality/latency-by-mode-route`
- `/execution/quality/drag-breakdown/latest`
- `/execution/quality/symbol-leakage/latest`

## Required Baseline Fields

### Slippage by mode

From `/execution/quality/by-mode`:

- `mode`
- `avg_slippage_bps`
- `run_id`
- `cycle_id`

### Slippage by route

From `/execution/quality/route-leakage/latest`:

- `route`
- `avg_slippage_bps`
- `execution_drag_usd`
- `notional_share`

### Latency by mode and route

From `/execution/quality/latency-by-mode-route`:

- `mode`
- `route`
- `avg_latency_ms`
- `latency_ms_p50`
- `latency_ms_p95`

### Execution drag percentage

From `/execution/quality/drag-breakdown/latest`:

- `gross_alpha_pnl_usd`
- `execution_drag_usd`

Derived baseline:

```text
execution_drag_pct = execution_drag_usd / gross_alpha_pnl_usd
```

### Top leakage symbols

From `/execution/quality/symbol-leakage/latest`:

- ordered by `execution_drag_usd`
- report the top symbols with:
  - `symbol`
  - `execution_drag_usd`
  - `notional_share`

### Top leakage routes

From `/execution/quality/route-leakage/latest`:

- ordered by `execution_drag_usd`
- report the top routes with:
  - `route`
  - `execution_drag_usd`
  - `notional_share`

## Coherence Rules

The baseline set is acceptable when:

- mode slippage rows exist for the active modes under test
- route leakage rows exist for the latest run
- latency rows preserve `latency_ms_p95 >= latency_ms_p50`
- symbol leakage totals match latest run `execution_drag_usd`
- route leakage totals match latest run `execution_drag_usd`
- `gross_alpha_pnl_usd > 0`
- `execution_drag_pct >= 0`

## Meaning

This baseline is the reference frame for future optimization work.

It answers:

- what current execution costs look like
- where current leakage concentrates
- what future improvements should be compared against

## Non-Goals

This baseline does not yet:

- optimize any metric
- recalibrate any market model
- choose the next lane

It only fixes the starting measurement frame for `Execution Reality v1`.
