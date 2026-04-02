# Portfolio Intelligence Packet 04 Plan

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Status: `defined`

## Packet

`PI-04 - Allocation Tradeoff Resolution`

## Why This Packet Exists

`PI-01` to `PI-03` made portfolio allocation execution-aware, control-aware, and stability-visible.

The next gap is no longer visibility.

The gap is:

- when `conviction`, `execution drag`, `exposure concentration`, `stability`, and `control state` disagree, how does portfolio choose one resolved allocation action?

## New Surface

- `GET /portfolio/intelligence/allocation-tradeoff/latest`

## Invariant

The latest portfolio intelligence surface must resolve competing allocation pressures into one deterministic action per governed symbol.

## Required Fields

Each item must expose:

- `symbol`
- `current_weight`
- `target_weight_after_control`
- `previous_target_weight`
- `target_weight_delta`
- `resolved_allocation_action`
- `resolved_target_weight`
- `tradeoff_score`
- `tradeoff_breakdown`
- `tradeoff_reason_codes`
- `previous_resolved_allocation_action`
- `action_changed`

## Resolution Vocabulary

The resolved action model is:

- `increase`
- `hold`
- `trim`
- `zero`
- `defer`

## Acceptance

The packet is acceptable when:

1. one resolved allocation action is emitted per symbol
2. conflicting pressures are resolved deterministically
3. `tradeoff_breakdown` makes the winning pressure visible
4. consecutive runs explain why a symbol moved from previous action to current action
5. rationale is explicit enough for operator and audit review without reopening prior lanes
