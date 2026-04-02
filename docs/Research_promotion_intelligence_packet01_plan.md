# Research / Promotion Intelligence Packet 01

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Research / Promotion Intelligence`
Packet: `01`
Status: `defined`

## Goal

Start the next lane by converting the `effective selection slate` into an explicit research/promotion agenda.

## Invariant

`/research-factory/intelligence/promotion-agenda/latest` must return one deterministic `promotion_action` per alpha.

## Acceptance

The packet is acceptable when:

- the surface returns `effective_status`, `promotion_action`, `promotion_rationale`, and `review_priority`
- `promotion_action` is one of `promote / advance / stay_queued / demote / retire`
- `selected_for_promotion_review` maps to `promote`
- `selected_for_shadow_review` maps to `advance`
- `returned_to_research` can map to `stay_queued` or `demote`
- low-quality deferred candidates can map to `retire`

## Route

- `GET /research-factory/intelligence/promotion-agenda/latest`
