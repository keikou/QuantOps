# Policy Optimization / Meta-Control Learning Packet 03

Date: `2026-04-03`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `PO-03`
Title: `Persisted Meta-Policy State`

## Why This Packet Exists

`PO-02` resolves family-level tuning recommendations.

The next boundary is to persist those recommendations as explicit meta-policy state so later packets can compare, consume, and optimize them over time.

## Core Invariant

For each family-level tuning recommendation, the repo must expose a persisted meta-policy state that:

- has a stable state id
- links to the previous meta-policy state for the same family
- carries the resolved tuning action and adjustments
- records the source packet that produced the state

## Canonical Surface

- `GET /system/meta-policy-state/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `meta_policy_state_id`
- `previous_meta_policy_state_id`
- `tuning_action`
- `tuning_adjustments.threshold_adjustment`
- `tuning_adjustments.weight_adjustment`
- `tuning_adjustments.escalation_rule`
- `policy_source_packet`
- `persisted_meta_policy_summary.system_meta_policy_action`

## Acceptance

`PO-03` is acceptable when:

- each family gets one persisted meta-policy state
- previous vs current state linkage is explicit
- the state remains deterministic and family-scoped
- the payload is sufficient for later cross-cycle comparison
