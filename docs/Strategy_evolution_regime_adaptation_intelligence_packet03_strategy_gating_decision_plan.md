# Strategy Evolution / Regime Adaptation Intelligence Packet 03

Date: `2026-04-23`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `SERI-03`
Title: `Strategy Gating Decision`

## Why This Packet Exists

`SERI-02` makes family compatibility explicit.

The next boundary is to convert compatibility into one deterministic strategy gating decision per family.

## Core Invariant

Once regime mismatch is explicit, the system should emit one stable gating decision instead of leaving regime response implicit.

## Canonical Surface

- `GET /system/strategy-gating-decision/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `strategy_gating_decision`
- `gating_reason`
- `gating_reason_codes`
- `strategy_gating_decision_summary.system_strategy_gating_action`

## Acceptance

`SERI-03` is acceptable when:

- each family receives one deterministic gating decision
- regime incompatibility no longer stays only as a descriptive compatibility view
- one stable system-level gating action is emitted
