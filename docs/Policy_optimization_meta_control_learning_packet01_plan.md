# Policy Optimization / Meta-Control Learning Packet 01

Date: `2026-04-03`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `PO-01`
Title: `Multi-cycle Policy Effectiveness Attribution`

## Why This Packet Exists

`SLLFI v1` closed the first loop where learning feedback becomes persisted policy state, resolved override, and next-cycle consumed behavior.

That means the next question is no longer whether the system can apply learned policy.

The next question is whether the applied policy actually improves downstream outcomes over time.

## Core Invariant

For each consumed override family, the repo must expose a stable surface that:

- measures downstream effect after applied override consumption
- attributes the effect to the applied policy path, not only to raw market movement
- classifies policy effect as `beneficial`, `neutral`, or `adverse`
- keeps the attribution family-scoped and multi-cycle-aware

## Canonical Surface

- `GET /system/policy-effectiveness/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `observed_policy_cycles`
- `consumed_effect`
- `effect_classification`
- `intended_vs_realized`
- `policy_paths.selection`
- `policy_paths.capital`
- `policy_paths.review`
- `policy_paths.runtime`
- `downstream_feedback`
- `attribution_reason_codes`
- `policy_effectiveness_summary.system_policy_optimization_action`

## Attribution Rule

This packet does not claim pure causal inference.

It makes a narrower and stable claim:

- policy effectiveness is attributed through the applied policy path
- downstream outcome is read from the already-governed portfolio and learning surfaces
- multi-cycle evidence is represented by observed persisted policy states for the same family

## Acceptance

`PO-01` is acceptable when:

- family-level policy effectiveness is explicit
- `beneficial / neutral / adverse` is deterministic
- selection/capital/review/runtime paths are visible in one item
- multi-cycle policy history is visible through `observed_policy_cycles`
- the surface produces a stable system-level optimization action
