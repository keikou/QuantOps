# Meta Portfolio Intelligence / Cross-Strategy Capital Allocation Packet 02

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `MPI-02`
Title: `Meta Portfolio Decision Surface`

## Why This Packet Exists

`MPI-01` makes family-level capital competition explicit.

The next boundary is to convert target share differences into one deterministic meta-portfolio decision per family.

## Core Invariant

Once cross-strategy capital competition is explicit, the repo must produce one stable decision that says whether each family should `shift`, `rebalance`, `hold`, or `freeze`.

## Canonical Surface

- `GET /system/meta-portfolio-decision/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `current_allocation_share`
- `target_allocation_share`
- `meta_portfolio_decision`
- `decision_reason`
- `capital_flow_hint`
- `meta_portfolio_decision_summary.system_meta_portfolio_decision_action`

## Acceptance

`MPI-02` is acceptable when:

- family-level capital movement is no longer only descriptive
- one deterministic decision exists per family
- material rebalance families are countable
- one stable system-level meta-portfolio decision action is produced
