# Governance -> Runtime Control Packet 06

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Governance -> Runtime Control`
Status: `packet_c6_defined`

## Packet

`C6: Cross-Control Policy Arbitration`

## Why This Packet Exists

`C1` through `C5` made route, slippage, latency, symbol, and adaptive control explicit.

The next unresolved question is:

- how do multiple control outputs resolve into one authoritative runtime action?

Without arbitration, the system can expose conflicting instructions such as:

- `degrade` from route leakage
- `stop` from latency
- `zero` from symbol capital
- `block` from adaptive feedback

That is not yet a stable runtime contract.

## Invariant

Multiple active control signals for the same run must resolve into exactly one deterministic runtime action per route.

## Required Surfaces

- `GET /governance/runtime-control/policy-arbitration/latest`
- `POST /governance/runtime-control/policy-arbitration/apply`

## Required Behavior

- route, slippage, latency, symbol, and adaptive controls may coexist
- each active route must emit exactly one `resolved_runtime_action`
- precedence must be deterministic
- conflicts must be explicit rather than hidden
- the resolved action must include its winning control family and packet source
- applied arbitration results must be written to `audit_logs`

## Fixed Precedence

Resolved action precedence is fixed as:

- `halt`
- `stop`
- `block`
- `zero`
- `pause`
- `throttle`
- `trim`
- `degrade`
- `allow`

Compatibility aliases:

- `keep -> allow`
- `continue -> allow`

## Acceptance Shape

The packet is accepted when:

- a latest run can expose competing controls for the same route
- arbitration returns one resolved row per route
- each resolved row includes `resolution_source_packet`, `resolution_source`, `raw_controls`, `conflicts`, and `has_conflict`
- precedence picks the expected winner
- `apply` persists one `policy_arbitration_resolution` audit row per resolved route

## Verifier

- `test_bundle/scripts/verify_governance_runtime_control_packet06_cross_control_policy_arbitration.py`
