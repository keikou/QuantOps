# Live Capital Control / Adaptive Runtime Allocation Packet 04

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `LCC-04`
Title: `Live Capital Control Consumption`

## Why This Packet Exists

`LCC-03` persists live capital control state.

The next boundary is to show how that control state is actually consumed as live budget and risk usage.

## Core Invariant

For each live family, persisted control state must map into explicit live capital and risk consumption.

## Canonical Surface

- `GET /system/live-capital-control-consumption/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `control_state`
- `live_capital_control_consumption.used_capital`
- `live_capital_control_consumption.used_risk`
- `live_capital_control_consumption.headroom`
- `live_capital_control_consumption.utilization_ratio`
- `live_capital_control_consumption_summary.system_consumption_action`

## Acceptance

`LCC-04` is acceptable when:

- each live family exposes actual budget consumption
- frozen state consumes zero budget
- reduced or degraded state consumes reduced budget
- headroom and utilization are explicit
