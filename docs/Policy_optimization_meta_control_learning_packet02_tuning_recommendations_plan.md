# Policy Optimization / Meta-Control Learning Packet 02

Date: `2026-04-03`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `PO-02`
Title: `Policy Tuning Recommendations`

## Why This Packet Exists

`PO-01` makes policy effectiveness explicit.

The next boundary is to convert that effectiveness reading into deterministic tuning guidance that can later be persisted or consumed by a higher-order policy controller.

## Core Invariant

For each family-level policy effectiveness item, the repo must expose a stable tuning recommendation that:

- resolves into `reinforce / hold / retune`
- carries explicit threshold and weight adjustments
- includes one escalation rule
- stays attributable to the existing `PO-01` policy path evidence

## Canonical Surface

- `GET /system/policy-tuning/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `effect_classification`
- `tuning_action`
- `tuning_adjustments.threshold_adjustment`
- `tuning_adjustments.weight_adjustment`
- `tuning_adjustments.escalation_rule`
- `tuning_summary.system_tuning_action`

## Acceptance

`PO-02` is acceptable when:

- beneficial families become `reinforce`
- adverse families become `retune`
- neutral families remain `hold`
- the tuning surface remains deterministic and family-scoped
- the system-level tuning action is stable
