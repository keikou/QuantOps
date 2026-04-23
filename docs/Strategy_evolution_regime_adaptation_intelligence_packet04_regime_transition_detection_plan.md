# Strategy Evolution / Regime Adaptation Intelligence Packet 04

Date: `2026-04-23`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `SERI-04`
Title: `Regime Transition Detection`

## Why This Packet Exists

`SERI-03` makes family gating decisions explicit.

The next boundary is to detect whether regime change is emerging or confirmed rather than treating each gating outcome as an isolated event.

## Core Invariant

Regime shift should be detected as a transition process, not only as a one-cycle compatibility or gating snapshot.

## Canonical Surface

- `GET /system/regime-transition-detection/latest`

## What The Surface Must Return

The latest payload must include:

- `run_id / cycle_id / consumed_run_id / consumed_cycle_id`
- `items[]` grouped by `alpha_family`
- `regime_transition_detection.transition_detected`
- `regime_transition_detection.detection_strength`
- `regime_transition_detection.previous_family_regime_state`
- `regime_transition_detection.previous_strategy_gating_decision`
- `regime_transition_detection.transition_reason`
- `regime_transition_detection_summary.system_regime_transition_action`

## Acceptance

`SERI-04` is acceptable when:

- transition is detected from current and prior regime posture rather than from thread memory
- family-level transition strength is explicit
- one stable system-level transition action is emitted
