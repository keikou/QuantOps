# Meta Portfolio Intelligence / Cross-Strategy Capital Allocation Packet 05

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `MPI-05`
Title: `Meta Portfolio Efficiency`

## Why This Packet Exists

`MPI-04` makes cross-strategy capital flow explicit.

The next boundary is to evaluate whether that flow improved the meta-portfolio allocation quality.

## Core Invariant

Cross-strategy capital movement must be evaluable as `beneficial`, `neutral`, or `adverse` against marginal opportunity quality.

## Canonical Surface

- `GET /system/meta-portfolio-efficiency/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `meta_portfolio_flow`
- `intended_objective`
- `realized_effect`
- `efficiency_reason_codes`
- `meta_portfolio_efficiency_summary.system_meta_portfolio_efficiency_action`

## Acceptance

`MPI-05` is acceptable when:

- meta-portfolio flow is outcome-evaluable
- beneficial vs neutral vs adverse families are countable
- one stable system-level efficiency action is produced
- the first meta-portfolio checkpoint can be judged from explicit outcome data
