# Governance Runtime Control Packet 04

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Governance -> Runtime Control`
Status: `packet_c4_defined`

## Packet

`C4: Symbol-level capital reallocation`

## Invariant

Latest symbol leakage evidence for the active run must become explicit keep, trim, or zero capital guidance instead of remaining as passive attribution only.

## Required Surface

- `GET /governance/runtime-control/symbol-reallocation/latest`

## Required Behavior

- latest symbol leakage rows stay bound to the latest active run
- each symbol returns one of `keep / trim / zero`
- each symbol returns `target_capital_multiplier`
- decisioning uses explicit symbol drag and notional concentration thresholds

## Fixed Thresholds

- `trim_symbol_drag_usd = 3.0`
- `zero_symbol_drag_usd = 5.0`
- `trim_symbol_notional_share = 0.30`
- `zero_symbol_notional_share = 0.45`

## Verifier

- `test_bundle/scripts/verify_governance_runtime_control_packet04_symbol_reallocation.py`

## Notes

This packet does not yet rewrite portfolio weights. It proves that symbol-level execution drag can become explicit capital guidance for the next runtime control layer.
