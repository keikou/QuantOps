# Meta Portfolio Intelligence / Cross-Strategy Capital Allocation Packet 03

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `MPI-03`
Title: `Meta Portfolio State`

## Why This Packet Exists

`MPI-02` makes meta-portfolio decisions explicit.

The next boundary is to persist those decisions as auditable state so the next cycle can consume them.

## Core Invariant

Once meta-portfolio decisions exist, the repo must persist one stable state per family that records the current cross-strategy capital posture.

## Canonical Surface

- `GET /system/meta-portfolio-state/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `meta_portfolio_decision`
- `meta_portfolio_state`
- `meta_portfolio_state_id`
- `previous_meta_portfolio_state_id`
- `last_meta_portfolio_tick`
- `meta_portfolio_state_summary.system_meta_portfolio_state_action`

## Acceptance

`MPI-03` is acceptable when:

- meta-portfolio decisions are no longer transient
- family-level state is auditable
- balanced vs concentrated vs unstable vs frozen families are countable
- one stable system-level state action is produced
