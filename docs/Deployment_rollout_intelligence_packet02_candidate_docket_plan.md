# Deployment / Rollout Intelligence Packet 02

Date: `2026-04-04`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `DRI-02`
Title: `Rollout Candidate Docket`

## Why This Packet Exists

`DRI-01` makes rollout stage selection explicit.

The next boundary is to package those stage decisions into a reviewable docket so rollout does not remain an unstructured recommendation surface.

## Core Invariant

For each `DRI-01` rollout decision item, the repo must expose a candidate docket that:

- keeps the staged rollout linkage
- resolves one `deployment_action`
- resolves one `approval_status`
- classifies the item into one `docket_status`
- attaches completed-checkpoint lineage for operator review
- produces one stable system-level docket action

## Canonical Surface

- `GET /system/deployment-rollout-candidate-docket/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `recommended_rollout_stage`
- `rollout_eligibility`
- `approval_status`
- `docket_status`
- `deployment_action`
- `rollout_priority`
- `checkpoint_lineage`
- `candidate_docket_summary.system_docket_action`

## Docket Mapping

`DRI-02` should apply deterministic docket mapping:

- blocked items -> `blocked_candidate`
- limited eligible items -> `limited_rollout_candidate`
- canary eligible items -> `canary_rollout_candidate`
- full eligible items -> `full_rollout_candidate`
- hold items -> `evidence_hold_candidate`

## Acceptance

`DRI-02` is acceptable when:

- ready, pending, and denied families are countable
- docket status is deterministic
- deployment action is explicit
- completed-checkpoint lineage is attached
- one stable system docket action is emitted
