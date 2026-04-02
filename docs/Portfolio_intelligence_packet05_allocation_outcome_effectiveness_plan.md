# Portfolio Intelligence Packet 05 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Status: `defined`

## Packet

`PI-05 - Allocation Outcome Effectiveness`

## Why This Packet Exists

`PI-04` made portfolio allocation tradeoffs deterministic and explainable.

The next gap is no longer:

- why the allocator chose a resolved action

The next gap is:

- whether the resolved action actually improved the portfolio outcome it was meant to improve

## New Surface

- `GET /portfolio/intelligence/allocation-outcome-effectiveness/latest`

## Invariant

The latest portfolio intelligence surface must evaluate previous resolved allocation actions against the next run's realized portfolio response.

## Required Fields

Each item must expose:

- `symbol`
- `source_run_id`
- `evaluated_run_id`
- `previous_resolved_allocation_action`
- `current_resolved_allocation_action`
- `intended_objective`
- `drag_change_usd`
- `resolved_weight_change`
- `concentration_change`
- `previous_stability_state`
- `current_stability_state`
- `realized_effect`
- `realized_reason_codes`

## Effect Vocabulary

The realized effect model is:

- `beneficial`
- `neutral`
- `adverse`

## Acceptance

The packet is acceptable when:

1. previous resolved actions are explicitly evaluated on the next run
2. intended objective and realized effect are both visible
3. drag, exposure, concentration, and stability deltas are explicit
4. `policy_effectiveness_summary` is available
5. the result explains whether portfolio policy is only coherent or also outcome-evaluable
