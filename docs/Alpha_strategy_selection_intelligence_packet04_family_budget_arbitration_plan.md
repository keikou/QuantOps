# Alpha / Strategy Selection Intelligence Packet 04

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha / Strategy Selection Intelligence`
Packet: `04`
Status: `defined`

## Goal

Prevent same-family alpha candidates from overrunning the same queue by applying a deterministic family budget.

## Invariant

`/alpha/intelligence/family-budget-arbitration/latest` must return one arbitrated queue decision per alpha with explicit family rank and budget state.

## Acceptance

The packet is acceptable when:

- the surface returns `queue_name`, `arbitrated_queue_name`, `family_budget_state`, `family_rank`, and `winning_in_family`
- at most one alpha per family can remain in `promotion_candidate`
- at most one alpha per family can remain in `shadow_review`
- over-budget peers are deterministically pushed down to the fallback queue
- a verifier can seed multiple same-family shadow candidates and confirm only one survives the family budget

## Route

- `GET /alpha/intelligence/family-budget-arbitration/latest`
