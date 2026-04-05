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

## Design Rule

`SERI` should distinguish regime-consistent degradation from stochastic noise.

No strategy should continue to receive normal treatment once the system has enough evidence that mismatch is regime-driven rather than incidental.
