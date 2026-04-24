# ASD-04 LLM-Assisted Hypothesis Generator

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Packet: `ASD-04`
Status: `implemented`

## Goal

Turn regime-conditioned search intent into explicit hypothesis briefs and constrained prompt packs so the system can translate hypothesis intent into symbolic alpha drafts without depending on an unbounded template replay loop.

## Scope

`ASD-04` adds:

- regime-conditioned hypothesis agenda
- constrained LLM-style prompt packs
- translated symbolic candidates
- hypothesis critique
- hypothesis effectiveness

## Canonical Outputs

1. `GET /system/alpha-hypothesis-agenda/latest`
2. `GET /system/alpha-llm-hypothesis-prompts/latest`
3. `GET /system/alpha-llm-translation-candidates/latest`
4. `GET /system/alpha-hypothesis-critique/latest`
5. `GET /system/alpha-hypothesis-effectiveness/latest`

## Implementation Notes

- hypothesis briefs are derived from `ASD-03` regime agenda and family expression map
- prompt packs remain deterministic and DSL-constrained inside repo runtime
- translated candidates are persisted through the `alpha_synthesis` run/candidate flow with generator type `hypothesis`
- critique combines validation status, novelty, and regime-fit posture

## Verifier

- `test_bundle/scripts/verify_alpha_synthesis_structural_discovery_intelligence_packet04.py`
