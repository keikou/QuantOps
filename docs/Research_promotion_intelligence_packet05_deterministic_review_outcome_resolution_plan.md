# Research / Promotion Intelligence Packet 05

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Research / Promotion Intelligence`
Packet: `05`
Status: `defined`

## Goal

Resolve the board-facing review slate into deterministic applied review outcomes.

## Invariant

`/research-factory/intelligence/deterministic-review-outcomes/latest` must return one deterministic `resolved_review_outcome` per board slate item.

## Acceptance

The packet is acceptable when:

- the surface returns `previous_review_status`, `resolved_review_outcome`, `outcome_reason_code`, and `downstream_target_state`
- `approve_shadow_review` can resolve to `shadow`
- `approve_retirement_review` can resolve to `retire`
- `hold` can resolve to `needs_more_evidence`
- `return_to_research` can resolve to `defer`
- the surface exposes an `outcome_summary`
- a verifier can confirm representative mappings and summary counts

## Route

- `GET /research-factory/intelligence/deterministic-review-outcomes/latest`
