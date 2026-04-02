# Governance Runtime Control Packet 05

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Governance -> Runtime Control`
Status: `packet_c5_defined`

## Packet

`C5: Closed-Loop Adaptive Control`

## Invariant

Route-level control decisions must be logged with outcomes, and the next run must be able to adapt routing control from prior control effectiveness instead of using only static thresholds.

## Required Surfaces

- `GET /governance/runtime-control/closed-loop/latest`
- `POST /governance/runtime-control/closed-loop/apply`

## Required Behavior

- current route routing control is still derived from latest execution leakage
- previous adaptive feedback for the same route is loaded from persisted control history
- next-run decisions can `relax` after improvement or `escalate` after failed degrade
- cooldown and hysteresis fields are explicit so routes do not flip immediately inside the same run

## Minimum Adaptive Signals

- `previous_decision`
- `previous_observed_slippage_bps`
- `delta_slippage_bps`
- `adaptation_state`
- `adaptive_target_weight_multiplier`

## Verifier

- `test_bundle/scripts/verify_governance_runtime_control_packet05_closed_loop_adaptive_control.py`

## Notes

This first closed-loop packet is intentionally route-scoped. It proves the adaptive loop exists before extending the same pattern to symbol capital, throttling, or regime-aware policy updates.
