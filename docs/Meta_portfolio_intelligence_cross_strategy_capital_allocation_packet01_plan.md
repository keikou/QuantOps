# Meta Portfolio Intelligence / Cross-Strategy Capital Allocation Packet 01

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `MPI-01`
Title: `Capital Competition Engine`

## Why This Packet Exists

`LCC-05` proves that live capital can be controlled and evaluated per family.

The next boundary is to decide which live families should win more capital when multiple families compete for the same budget.

## Core Invariant

Total capital must be continuously reallocated to the highest marginal risk-adjusted opportunity across all live strategies.

## Canonical Surface

- `GET /system/meta-portfolio-allocation/latest`

## What The Surface Must Return

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `current_allocation_share`
- `target_allocation_share`
- `allocation_share_delta`
- `marginal_efficiency_score`
- `allocation_action`
- `meta_portfolio_allocation_summary.system_meta_portfolio_action`

## Acceptance

`MPI-01` is acceptable when:

- family-level capital competition is explicit
- current share vs target share is deterministic
- reallocation winners and losers are countable
- one stable system-level meta-portfolio action is produced
