# AAE-01 Alpha Discovery And Validation Loop

Date: `2026-04-24`
Repo: `QuantOps_github`
Lane: `Autonomous Alpha Expansion / Strategy Generation Intelligence`
Packet: `AAE-01`
Status: `active_packet_boundary`

## Task

Make the alpha expansion loop explicit enough that a future thread can answer:

- which alpha candidates are being discovered now
- which candidates have actually passed validation
- which candidates should be admitted, shadowed, held, or rejected
- whether the inventory is healthy enough to replace dead alpha

## Required Output

Produce:

- one packet plan doc
- one verifier script
- explicit `/system/*` surfaces for discovery, validation, admission, lifecycle, and inventory health

## Current Canonical Surfaces

- `GET /system/alpha-discovery-candidates/latest`
- `GET /system/alpha-validation-results/latest`
- `GET /system/alpha-admission-decision/latest`
- `GET /system/alpha-lifecycle-state/latest`
- `GET /system/alpha-inventory-health/latest`

## Dependency Boundary

Depend on completed checkpoints only:

- `Alpha / Strategy Selection Intelligence v1` through `ASI-05`
- `Research / Promotion Intelligence v1` through `RPI-06`
- `Strategy Evolution / Regime Adaptation Intelligence v1` through `SERI-05`

## Verifier

- `test_bundle/scripts/verify_autonomous_alpha_expansion_strategy_generation_intelligence_packet01.py`
