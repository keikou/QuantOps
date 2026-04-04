# Deployment / Rollout Intelligence Packet 03

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `DRI-03`
Title: `Persisted Rollout State`

## Why This Packet Exists

`DRI-02` resolves rollout candidates into a reviewable docket.

The next boundary is to persist those rollout decisions as explicit state so later rollout packets can consume, compare, approve, or roll back against a stable baseline.

## Core Invariant

For each rollout candidate docket item, the repo must expose a persisted rollout state that:

- has a stable rollout state id
- links to the previous rollout state for the same family
- carries the resolved rollout stage and docket action
- records the source packet that produced the state

## Canonical Surface

- `GET /system/deployment-rollout-state/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `rollout_state_id`
- `previous_rollout_state_id`
- `recommended_rollout_stage`
- `rollout_eligibility`
- `approval_status`
- `docket_status`
- `deployment_action`
- `rollout_source_packet`
- `persisted_rollout_state_summary.system_rollout_state_action`

## Acceptance

`DRI-03` is acceptable when:

- each family gets one persisted rollout state
- previous vs current state linkage is explicit
- rollout state remains deterministic and family-scoped
- the payload is sufficient for later rollout consumption or rollback comparison
