# Strategy Evolution / Regime Adaptation Intelligence Packet 02

Date: `2026-04-23`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `SERI-02`
Title: `Strategy Regime Compatibility Surface`

## Why This Packet Exists

`SERI-01` makes current regime state explicit.

The next boundary is to show whether each family is compatible with that regime strongly enough to support later gating decisions.

## Core Invariant

No strategy family should be treated as equally eligible when the current regime state shows clear mismatch pressure.

## Canonical Surface

- `GET /system/strategy-regime-compatibility/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `compatibility_status`
- `compatibility_score`
- `recommended_posture`
- `compatibility_reason_codes`
- `strategy_regime_compatibility_summary.system_strategy_regime_action`

## Acceptance

`SERI-02` is acceptable when:

- compatibility is derived from current regime state rather than thread memory
- family-level compatibility is deterministic enough to support later gating decisions
- one stable system-level compatibility action is emitted
