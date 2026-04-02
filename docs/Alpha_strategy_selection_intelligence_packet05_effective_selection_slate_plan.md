# Alpha / Strategy Selection Intelligence Packet 05

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha / Strategy Selection Intelligence`
Packet: `05`
Status: `defined`

## Goal

Collapse the arbitrated queue output into one effective operator-facing selection slate.

## Invariant

`/alpha/intelligence/effective-selection-slate/latest` must return one effective status per alpha after family budget arbitration.

## Acceptance

The packet is acceptable when:

- the surface returns `arbitrated_queue_name` and `effective_status`
- `promotion_candidate` maps to `selected_for_promotion_review`
- `shadow_review` maps to `selected_for_shadow_review`
- `research_return` maps to `returned_to_research`
- `deferred_watchlist` maps to `deferred`
- the summary counts match the item-level effective statuses

## Route

- `GET /alpha/intelligence/effective-selection-slate/latest`
