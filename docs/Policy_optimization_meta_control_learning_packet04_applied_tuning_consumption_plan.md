# Policy Optimization / Meta-Control Learning Packet 04

Date: `2026-04-03`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `PO-04`
Title: `Applied Tuning Consumption`

## Why This Packet Exists

`PO-03` persists family-level meta-policy state.

The next boundary is to show that the persisted meta-policy is actually consumed by the next cycle, not only stored.

## Core Invariant

For each persisted meta-policy state, the repo must expose a next-cycle consumption surface that:

- keeps family-level state linkage
- shows the applied threshold and weight adjustments
- shows the applied escalation rule
- resolves into one deterministic consumed effect

## Canonical Surface

- `GET /system/meta-policy-consumption/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `meta_policy_state_id`
- `applied_tuning_consumption`
- `applied_tuning_consumption.applied_threshold_adjustment`
- `applied_tuning_consumption.applied_weight_adjustment`
- `applied_tuning_consumption.applied_escalation_rule`
- `consumed_effect`
- `applied_tuning_consumption_summary.system_consumption_action`

## Acceptance

`PO-04` is acceptable when:

- persisted meta-policy state is visibly consumed next cycle
- family-level consumption is deterministic
- the system-level consumption action is stable
- the packet is sufficient for later outcome evaluation
