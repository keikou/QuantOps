# Live Capital Control / Adaptive Runtime Allocation Packet 05

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `LCC-05`
Title: `Live Capital Control Effectiveness`

## Why This Packet Exists

`LCC-04` makes live capital control consumption explicit.

The next boundary is to evaluate whether the consumed live capital control posture produced useful runtime effect.

## Core Invariant

For each consumed live-capital control item, the repo must expose an effectiveness surface that:

- keeps the control-consumption linkage
- states the intended live-capital objective
- classifies realized effect as `beneficial`, `neutral`, or `adverse`
- produces one stable system-level effectiveness action

## Canonical Surface

- `GET /system/live-capital-control-effectiveness/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `control_state`
- `live_capital_control_consumption`
- `intended_objective`
- `realized_effect`
- `effectiveness_reason_codes`
- `live_capital_control_effectiveness_summary.system_effectiveness_action`

## Acceptance

`LCC-05` is acceptable when:

- consumed live-capital control is visibly evaluable
- realized effect is deterministic
- beneficial vs neutral vs adverse families are countable
- the system-level effectiveness action is stable
