# Governance Runtime Control Packet 03

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Governance -> Runtime Control`
Status: `packet_c3_defined`

## Packet

`C3: Latency-aware throttling`

## Invariant

Latest route-level latency evidence for the active run must be transformed into explicit throttle decisions instead of remaining as passive diagnostics only.

## Required Surface

- `GET /governance/runtime-control/latency-throttle/latest`

## Required Behavior

- latest execution quality summary binds the active `run_id / cycle_id / mode`
- latest `mode x route` latency rows for that run stay separated
- each route returns one of `allow / throttle / stop`
- each route returns `participation_rate_multiplier` and `slice_interval_multiplier`

## Fixed Thresholds

- `throttle_avg_latency_ms = 30.0`
- `stop_avg_latency_ms = 50.0`
- `throttle_p95_latency_ms = 60.0`
- `stop_p95_latency_ms = 90.0`

## Verifier

- `test_bundle/scripts/verify_governance_runtime_control_packet03_latency_throttle.py`

## Notes

This packet does not yet re-plan capital or route selection. It only proves that latency evidence can become explicit runtime throttling guidance for the active run.
