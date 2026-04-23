# SERI Regime Adaptation Contracts

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `initial_seri_contract_stub`

## Purpose

This file is the compact contract stub for `Strategy Evolution / Regime Adaptation Intelligence`.

Use it before implementation when you need the expected surface family for `SERI-01` through `SERI-05`.

## Expected Surface Family

1. `GET /system/regime-state/latest`
2. `GET /system/strategy-regime-compatibility/latest`
3. `GET /system/strategy-gating-decision/latest`
4. `GET /system/regime-transition-detection/latest`
5. `GET /system/strategy-survival-analysis/latest`

## Expected Contract Progression

1. current regime classification
2. strategy-to-regime compatibility view
3. gating decision for each strategy family
4. transition detection between regimes
5. survival or retirement pressure view

## Packet 01 Expectation

`SERI-01` should expose `GET /system/regime-state/latest` as a deterministic summary surface.

Expected payload shape:

- top-level `status`
- `as_of` or equivalent timestamp
- `current_regime`
- `regime_confidence`
- `supporting_signals`
- one explicit `system_regime_action`

## Packet 02 Expectation

`SERI-02` should expose `GET /system/strategy-regime-compatibility/latest` as a deterministic family-compatibility surface.

Expected payload shape:

- top-level `status`
- `items[]` grouped by `alpha_family`
- `compatibility_status`
- `compatibility_score`
- `recommended_posture`
- `compatibility_reason_codes`
- one explicit `system_strategy_regime_action`

## Packet 03 Expectation

`SERI-03` should expose `GET /system/strategy-gating-decision/latest` as a deterministic family gating surface.

Expected payload shape:

- top-level `status`
- `items[]` grouped by `alpha_family`
- `strategy_gating_decision`
- `gating_reason`
- `gating_reason_codes`
- one explicit `system_strategy_gating_action`

## Packet 04 Expectation

`SERI-04` should expose `GET /system/regime-transition-detection/latest` as a deterministic transition surface.

Expected payload shape:

- top-level `status`
- `items[]` grouped by `alpha_family`
- `regime_transition_detection.transition_detected`
- `regime_transition_detection.detection_strength`
- `regime_transition_detection.previous_family_regime_state`
- `regime_transition_detection.previous_strategy_gating_decision`
- `regime_transition_detection.transition_reason`
- one explicit `system_regime_transition_action`

## Packet 05 Expectation

`SERI-05` should expose `GET /system/strategy-survival-analysis/latest` as a deterministic survival surface.

Expected payload shape:

- top-level `status`
- `items[]` grouped by `alpha_family`
- `strategy_survival_analysis.survival_posture`
- `strategy_survival_analysis.survival_reason`
- `strategy_survival_analysis.survival_reason_codes`
- one explicit `system_strategy_survival_action`

## Design Rule

`SERI` should distinguish regime-consistent degradation from stochastic noise.

No strategy should continue to receive normal treatment once the system has enough evidence that mismatch is regime-driven rather than incidental.
