# Live Capital Control / Adaptive Runtime Allocation Packet 01

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `LCC-01`
Title: `Live Allocation Governor`

## Why This Packet Exists

`DRI-05` makes rollout outcome effectiveness explicit.

The next boundary is to ensure that live allocation does not remain a stale static result after live truth has materially changed.

## Core Invariant

No live deployment may remain on a stale static allocation once live effectiveness, risk usage, or execution quality has materially changed.

## Canonical Surface

- `GET /system/live-capital-control/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `effective_live_capital`
- `risk_budget_cap`
- `current_mode`
- `allowed_scaling_band`
- `live_control_action`
- `current_limits`
- `current_health`
- `live_capital_control_summary.system_live_capital_action`

## Acceptance

`LCC-01` is acceptable when:

- live capital is shown as a function of current truth rather than rollout-starting state
- families can be deterministically classified into `live / degraded / frozen`
- capital cap, risk cap, and mode are explicit
- one stable system-level live-capital action is emitted
