# Research / Promotion Intelligence Packet 03

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Research / Promotion Intelligence`
Packet: `03`
Status: `defined`

## Goal

Convert the lineage-backed promotion candidate docket into explicit review queues.

## Invariant

`/research-factory/intelligence/review-queues/latest` must return one deterministic `review_queue` and `next_review_action` per docket item.

## Acceptance

The packet is acceptable when:

- the surface returns `docket_status`, `review_queue`, `next_review_action`, and `queue_priority`
- `promotion_candidate` maps to `promotion_review`
- `shadow_candidate` maps to `shadow_review`
- `demotion_candidate` maps to `demotion_review`
- `retirement_candidate` maps to `retirement_review`
- all other items fall back to `research_backlog`
- a verifier can confirm queue summary counts and representative item mappings

## Route

- `GET /research-factory/intelligence/review-queues/latest`
