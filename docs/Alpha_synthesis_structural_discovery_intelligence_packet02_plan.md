# Alpha Synthesis / Structural Discovery Intelligence Packet 02 Plan

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `ASD-02`
Status: `implemented`

## Intent

Extend the symbolic generator core from random search into evolutionary search by making:

- parent selection
- mutation generation
- crossover generation
- evolutionary search state
- evolutionary effectiveness

explicit at the system surface.

## Canonical Surfaces

1. `GET /system/alpha-parent-candidates/latest`
2. `GET /system/alpha-mutation-candidates/latest`
3. `GET /system/alpha-crossover-candidates/latest`
4. `GET /system/alpha-evolution-search-state/latest`
5. `GET /system/alpha-evolution-effectiveness/latest`

## Dependencies

- `ASD-01`
- `AAE-05`

## Verifier

- `test_bundle/scripts/verify_alpha_synthesis_structural_discovery_intelligence_packet02.py`
