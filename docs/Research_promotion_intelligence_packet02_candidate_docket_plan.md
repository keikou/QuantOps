# Research / Promotion Intelligence Packet 02

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Research / Promotion Intelligence`
Packet: `02`
Status: `defined`

## Goal

Attach research lineage to the promotion agenda and expose a reviewable candidate docket.

## Invariant

`/research-factory/intelligence/promotion-candidate-docket/latest` must return promotion-agenda decisions together with experiment/model lineage when available.

## Acceptance

The packet is acceptable when:

- the surface returns `promotion_action`, `experiment_id`, `model_id`, `lineage_ready`, and `docket_status`
- `promote` maps to `promotion_candidate`
- `advance` maps to `shadow_candidate`
- `demote` maps to `demotion_candidate`
- `retire` maps to `retirement_candidate`
- a verifier can seed experiment/model lineage for selected alphas and confirm the docket exposes it

## Route

- `GET /research-factory/intelligence/promotion-candidate-docket/latest`
