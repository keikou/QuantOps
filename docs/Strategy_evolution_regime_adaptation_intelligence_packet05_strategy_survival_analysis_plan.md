# Strategy Evolution / Regime Adaptation Intelligence Packet 05

Date: `2026-04-23`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `SERI-05`
Title: `Strategy Survival Analysis`

## Why This Packet Exists

`SERI-04` makes regime transition explicit.

The next boundary is to convert regime transition and gating posture into one explicit survival outcome for each family.

## Core Invariant

If regime mismatch persists, the system should emit survival pressure explicitly rather than relying on implied follow-up from earlier packets.

## Canonical Surface

- `GET /system/strategy-survival-analysis/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `strategy_survival_analysis.survival_posture`
- `strategy_survival_analysis.survival_reason`
- `strategy_survival_analysis.survival_reason_codes`
- `strategy_survival_analysis_summary.system_strategy_survival_action`

## Acceptance

`SERI-05` is acceptable when:

- each family receives one explicit survival posture
- survival pressure is derived from current transition and gating evidence
- one stable system-level survival action is emitted
