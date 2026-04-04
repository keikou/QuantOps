# Deployment / Rollout Intelligence Packet 04

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `DRI-04`
Title: `Applied Rollout Consumption`

## Why This Packet Exists

`DRI-03` persists family-level rollout state.

The next boundary is to show that the persisted rollout posture is actually consumed by the next cycle, not only stored.

## Core Invariant

For each persisted rollout state, the repo must expose a next-cycle rollout consumption surface that:

- keeps family-level rollout state linkage
- shows the applied rollout stage
- shows the applied approval and deployment action
- resolves into one deterministic consumed effect

## Canonical Surface

- `GET /system/deployment-rollout-consumption/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `rollout_state_id`
- `applied_rollout_consumption`
- `applied_rollout_consumption.applied_stage`
- `applied_rollout_consumption.applied_approval_status`
- `applied_rollout_consumption.applied_deployment_action`
- `consumed_effect`
- `applied_rollout_consumption_summary.system_consumption_action`

## Acceptance

`DRI-04` is acceptable when:

- persisted rollout state is visibly consumed next cycle
- family-level rollout consumption is deterministic
- the system-level consumption action is stable
- the packet is sufficient for later rollout outcome evaluation
