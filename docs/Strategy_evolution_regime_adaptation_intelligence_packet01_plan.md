# Strategy Evolution / Regime Adaptation Intelligence Packet 01

Date: `2026-04-23`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `SERI-01`
Title: `Regime Detection And Strategy Gating Engine`

## Why This Packet Exists

`MPI-05` makes cross-strategy capital efficiency explicit and `LCC-05` makes live capital effectiveness explicit.

The next boundary is to make current regime state explicit enough that later strategy compatibility and gating packets can act on one deterministic system regime rather than on scattered local signals.

## Core Invariant

No strategy may continue to receive capital if its performance degradation is regime-consistent rather than stochastic.

## Canonical Surface

- `GET /system/regime-state/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `family_regime_state`
- `regime_confidence`
- `supporting_signals`
- top-level `current_regime`
- top-level `system_regime_action`
- `regime_state_summary`

## Acceptance

`SERI-01` is acceptable when:

- regime state is derived from current live-capital and meta-portfolio truth rather than thread memory
- family-level regime evidence is explicit enough for later compatibility and gating packets
- one deterministic top-level regime classification is emitted
- one stable system-level regime action is emitted
