# Governance Runtime Control Packet 02

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Governance -> Runtime Control`
Status: `packet_c2_defined`

## Packet

`C2: Slippage guard integration`

## Invariant

Latest execution slippage evidence must be transformed into an explicit guard decision, and that decision must integrate with runtime control state.

## Required Surfaces

- `GET /governance/runtime-control/slippage-guard/latest`
- `POST /governance/runtime-control/slippage-guard/apply`

## Required Behavior

- latest execution quality summary exposes `run_id / cycle_id / mode / avg_slippage_bps`
- elevated slippage maps to `pause`
- critical slippage maps to `halt`
- apply writes runtime control state so downstream runtime and live execution see `paused` or `halted`

## Fixed Thresholds

- `pause_slippage_bps = 3.0`
- `halt_slippage_bps = 5.0`

## Verifier

- `test_bundle/scripts/verify_governance_runtime_control_packet02_slippage_guard.py`

## Notes

This packet is intentionally narrow. It does not yet reallocate capital or throttle routes dynamically. It only proves that execution evidence can trigger explicit runtime guard state.
