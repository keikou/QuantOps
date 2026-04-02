# Portfolio Intelligence Packet 02

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Portfolio Intelligence`
Status: `packet_pi02_defined`

## Packet

`PI-02: Execution-Aware Exposure Shaping`

## Why This Packet Exists

`PI-01` made symbol-level capital guidance explicit.

The next unresolved question is:

- how does symbol guidance become a coherent portfolio exposure policy?

Without this packet, portfolio intelligence can explain symbol multipliers but still cannot express:

- target gross exposure
- target net exposure
- exposure reduction implied by control-aware capital shaping

## Invariant

Latest portfolio exposure shaping must consume execution-aware capital allocation and emit deterministic portfolio-level target exposure plus symbol-level target weights.

## Required Surface

- `GET /portfolio/intelligence/exposure-shaping/latest`

## Required Behavior

- each active symbol emits one `target_weight_after_control`
- portfolio-level `target_gross_exposure` is explicit
- portfolio-level `target_net_exposure` is explicit
- target weights are derived from current exposure and PI-01 multipliers
- zeroed symbols contribute no target exposure
- the shaped portfolio remains internally coherent with its symbol rows

## Acceptance Shape

The packet is accepted when:

- the latest run produces a shaped portfolio payload
- each symbol row includes `current_weight`, `target_capital_multiplier`, and `target_weight_after_control`
- `target_gross_exposure` equals the sum of absolute symbol target weights
- `target_net_exposure` equals the signed sum of symbol target weights

## Verifier

- `test_bundle/scripts/verify_portfolio_intelligence_packet02_execution_aware_exposure_shaping.py`
