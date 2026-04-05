# Meta Portfolio Intelligence / Cross-Strategy Capital Allocation Packet 04

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `MPI-04`
Title: `Meta Portfolio Flow`

## Why This Packet Exists

`MPI-03` persists family-level meta-portfolio state.

The next boundary is to show how that state turns into explicit next-cycle capital movement.

## Core Invariant

Persisted meta-portfolio state must be consumable as explicit cross-strategy capital flow.

## Canonical Surface

- `GET /system/meta-portfolio-flow/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `meta_portfolio_state`
- `meta_portfolio_flow.from_share`
- `meta_portfolio_flow.to_share`
- `meta_portfolio_flow.moved_share`
- `meta_portfolio_flow.flow_action`
- `meta_portfolio_flow_summary.system_meta_portfolio_flow_action`

## Acceptance

`MPI-04` is acceptable when:

- persisted state becomes explicit capital movement
- family-level flow is deterministic
- rebalance vs shift vs remove flows are countable
- one stable system-level flow action is produced
