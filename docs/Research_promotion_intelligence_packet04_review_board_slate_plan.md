# Research / Promotion Intelligence Packet 04

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Research / Promotion Intelligence`
Packet: `04`
Status: `defined`

## Goal

Resolve review queues into an explicit board-facing review slate.

## Invariant

`/research-factory/intelligence/review-board-slate/latest` must return one deterministic `board_decision` per queued alpha.

## Acceptance

The packet is acceptable when:

- the surface returns `review_queue`, `board_decision`, `board_rationale`, and `board_priority`
- lineage-ready `shadow_review` items can map to `approve_shadow_review`
- `retirement_review` items map to `approve_retirement_review`
- backlog items can remain `hold` or return to research
- the surface exposes a `board_summary`
- a verifier can confirm representative item mappings and summary counts

## Route

- `GET /research-factory/intelligence/review-board-slate/latest`
