# Live Capital Control / Adaptive Runtime Allocation Packet 03

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `LCC-03`
Title: `Live Capital Control State`

## Why This Packet Exists

`LCC-02` resolves one capital adjustment decision per live family.

The next boundary is to persist the resulting control posture as explicit runtime state so later packets can consume, compare, and evaluate it.

## Core Invariant

For each live family, the repo must expose one persisted control state that links current runtime posture to the latest capital adjustment decision.

## Canonical Surface

- `GET /system/live-capital-control-state/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `control_state`
- `control_state_id`
- `previous_control_state_id`
- `decision_age_seconds`
- `last_control_tick`
- `stale_flag`
- `control_source_packet`
- `live_capital_control_state_summary.system_control_state_action`

## Acceptance

`LCC-03` is acceptable when:

- each family gets one persisted control state
- previous vs current state linkage is explicit
- `live / degraded / reduced / frozen` state is deterministic
- freshness metadata is explicit for later consumption
