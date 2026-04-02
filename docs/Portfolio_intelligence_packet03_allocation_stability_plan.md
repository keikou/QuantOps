# Portfolio Intelligence Packet 03

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Portfolio Intelligence`
Status: `packet_pi03_defined`

## Packet

`PI-03: Allocation Stability Across Runs`

## Why This Packet Exists

`PI-01` and `PI-02` made allocation and exposure shaping explicit.

The next unresolved question is:

- how stable are those shaped decisions across consecutive runs?

Without this packet, the repo can shape exposure but cannot yet show:

- whether target weights are oscillating
- whether the latest shape is stable relative to the prior run

## Invariant

Latest exposure shaping must be comparable to the previous run and must emit explicit per-symbol and portfolio-level stability deltas.

## Required Surface

- `GET /portfolio/intelligence/allocation-stability/latest`

## Required Behavior

- compare latest shaped portfolio to prior shaped portfolio
- emit `previous_target_weight` and `target_weight_delta`
- emit `stability_state`
- emit portfolio-level `gross_delta` and `net_delta`
- explicitly identify symbols with materially changed target weights

## Acceptance Shape

The packet is accepted when:

- the latest run can be compared to a previous shaped run
- symbol rows include current and previous target weight context
- portfolio-level deltas are explicit
- stable vs changed symbols are counted deterministically

## Verifier

- `test_bundle/scripts/verify_portfolio_intelligence_packet03_allocation_stability.py`
