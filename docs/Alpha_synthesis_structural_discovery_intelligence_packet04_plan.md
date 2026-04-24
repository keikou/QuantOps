# Alpha Synthesis / Structural Discovery Intelligence Packet 04 Plan

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `ASD-04`
Status: `implemented`

## Intent

Extend regime-conditioned symbolic synthesis into LLM-assisted hypothesis generation by making:

- hypothesis agenda
- hypothesis prompt packs
- LLM-translated symbolic candidates
- hypothesis critique
- hypothesis effectiveness

explicit at the system surface.

## Canonical Surfaces

1. `GET /system/alpha-hypothesis-agenda/latest`
2. `GET /system/alpha-llm-hypothesis-prompts/latest`
3. `GET /system/alpha-llm-translation-candidates/latest`
4. `GET /system/alpha-hypothesis-critique/latest`
5. `GET /system/alpha-hypothesis-effectiveness/latest`

## Dependencies

- `ASD-03`
- `SERI-05`

## Verifier

- `test_bundle/scripts/verify_alpha_synthesis_structural_discovery_intelligence_packet04.py`
