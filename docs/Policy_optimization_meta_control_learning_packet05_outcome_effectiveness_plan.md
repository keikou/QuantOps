# Policy Optimization / Meta-Control Learning Packet 05

Date: `2026-04-03`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `PO-05`
Title: `Meta-Policy Outcome Effectiveness`

## Why This Packet Exists

`PO-04` makes meta-policy consumption explicit.

The next boundary is to evaluate whether consumed meta-policy tuning actually produced useful downstream effect.

## Core Invariant

For each consumed meta-policy item, the repo must expose an outcome-effectiveness surface that:

- keeps the consumed tuning linkage
- states the intended objective
- classifies realized effect as `beneficial`, `neutral`, or `adverse`
- produces a stable system-level effectiveness action

## Canonical Surface

- `GET /system/meta-policy-effectiveness/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `tuning_action`
- `consumed_effect`
- `intended_objective`
- `realized_effect`
- `effectiveness_reason_codes`
- `outcome_effectiveness_summary.system_effectiveness_action`

## Acceptance

`PO-05` is acceptable when:

- the consumed tuning path is visibly evaluable
- realized effect is deterministic
- beneficial vs neutral vs adverse families are countable
- the system-level effectiveness action is stable
