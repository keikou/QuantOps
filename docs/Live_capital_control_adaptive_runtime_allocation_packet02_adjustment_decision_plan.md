# Live Capital Control / Adaptive Runtime Allocation Packet 02

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `LCC-02`
Title: `Live Capital Adjustment Decision`

## Why This Packet Exists

`LCC-01` makes live capital control state explicit.

The next boundary is to convert that control state into one deterministic capital adjustment decision per live family.

## Core Invariant

For each live strategy, current live control state must resolve into one deterministic capital adjustment decision from `keep / scale_up / scale_down / freeze / revert_to_shadow`.

## Canonical Surface

- `GET /system/live-capital-adjustment-decision/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `effective_live_capital`
- `current_mode`
- `capital_adjustment_decision`
- `decision_reason`
- `live_capital_adjustment_summary.system_adjustment_action`

## Acceptance

`LCC-02` is acceptable when:

- every live family maps to exactly one adjustment decision
- `frozen` state maps to `freeze` or `revert_to_shadow`
- degraded state maps to `scale_down`
- beneficial healthy live state can map to `scale_up`
- one stable system-level adjustment action is emitted
