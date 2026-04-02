# Portfolio Intelligence Packet 01

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Portfolio Intelligence`
Status: `packet_pi01_defined`

## Packet

`PI-01: Execution-Aware Capital Allocation Surface`

## Why This Packet Exists

`Execution Reality` and `Governance -> Runtime Control` are now explicit enough to act as inputs.

The next unresolved question is:

- how does portfolio allocation consume execution economics and resolved control state?

Without this packet, allocation still remains execution-blind even though the repo already knows:

- symbol-level leakage
- route-level arbitration
- guard and throttle state
- symbol capital guidance

## Invariant

Latest portfolio capital guidance must explicitly consume execution drag, leakage attribution, and resolved runtime control state, then emit deterministic symbol-level allocation multipliers.

## Required Surface

- `GET /portfolio/intelligence/execution-aware-capital/latest`

## Required Inputs

- latest portfolio overview or positions
- latest execution symbol leakage
- latest symbol capital guidance
- latest cross-control arbitration output
- latest slippage guard state

## Required Behavior

- each active symbol emits one allocation row
- each row includes current portfolio weight context
- each row includes execution leakage context
- each row includes relevant control context
- each row emits one `allocation_decision`
- each row emits one deterministic `target_capital_multiplier`
- severe global or route control must dominate weaker symbol-local hints

## Acceptance Shape

The packet is accepted when:

- the latest run produces explicit symbol-level rows
- the rows include `execution_drag_usd`, `notional_share`, `symbol_control_decision`, `resolved_control_action`, and `global_guard_decision`
- conflicting inputs resolve into one deterministic `allocation_decision`
- target multipliers remain bounded and explicit

## Verifier

- `test_bundle/scripts/verify_portfolio_intelligence_packet01_execution_aware_capital_allocation.py`
