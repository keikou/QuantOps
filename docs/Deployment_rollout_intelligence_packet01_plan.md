# Deployment / Rollout Intelligence Packet 01

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `DRI-01`
Title: `Staged Rollout Decision Surface`

## Why This Packet Exists

`PO-05` makes meta-policy outcome effectiveness explicit.

The next boundary is to decide how checkpoint-complete governed changes should be rolled out without replaying closed implementation lanes.

## Core Invariant

For each rollout candidate derived from completed checkpoint inputs, the repo must expose a staged rollout decision surface that:

- keeps the `PO-05` outcome linkage
- chooses one recommended rollout stage from `shadow / limited / canary / full`
- states whether the family is `eligible`, `hold`, or `blocked`
- makes gating conditions explicit
- makes rollback conditions explicit
- produces one stable system-level rollout action

## Canonical Surface

- `GET /system/deployment-rollout-decision/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `tuning_action`
- `realized_effect`
- `rollout_eligibility`
- `recommended_rollout_stage`
- `stage_reason_codes`
- `gating_conditions`
- `rollback_conditions`
- `rollout_decision_summary.system_rollout_action`

## Decision Logic

`DRI-01` should apply deterministic rollout staging:

- `adverse` effect or coherence failure -> `shadow`
- `neutral` effect -> `limited`
- `beneficial` effect with modest confirmation -> `canary`
- `beneficial` effect with stronger multi-cycle confirmation -> `full`

## Acceptance

`DRI-01` is acceptable when:

- rollout-eligible families are countable
- blocked families are countable
- recommended rollout stage is deterministic
- gating and rollback conditions are explicit
- one stable system rollout action is emitted
