# Task: SERI-01 Regime Detection And Strategy Gating Engine

Date: `2026-04-05`
Status: `active`

## Goal

Implement the first `Strategy Evolution / Regime Adaptation Intelligence` packet so the system can expose current regime state as a deterministic surface.

## Why Now

`Meta Portfolio Intelligence v1` is checkpoint-complete, and the architect-selected next top-level lane is now `SERI`.

The repo needs one explicit regime-state surface before compatibility, gating, transition, and survival layers can be built on top.

## Inputs

- `../03_plans/current.md`
- `../04_tasks/current.md`
- `../11_reports/current_status.md`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_checkpoint_v1.md`
- `../Live_capital_control_adaptive_runtime_allocation_checkpoint_v1.md`
- `../../apps/v12-api/ai_hedge_bot/api/routes/system.py`

## Steps

1. define the `SERI-01` packet plan doc
2. implement `GET /system/regime-state/latest`
3. add the narrow verifier for the new regime-state surface
4. update current docs so future threads see `SERI-01` as the concrete active task

## Outputs

- one `SERI-01` plan doc
- one `SERI-01` verifier script
- one regime-state system surface

## Non-Goals

- implementing the full `SERI` lane in one step
- replaying `MPI`, `LCC`, or `DRI`
- expanding unrelated docs restructuring in the same packet

## Completion Check

- `GET /system/regime-state/latest` exists
- one verifier covers the new packet
- docs point to `SERI-01` as an executable active task rather than only a lane name
