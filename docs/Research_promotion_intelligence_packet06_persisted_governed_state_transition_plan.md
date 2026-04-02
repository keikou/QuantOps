# Research / Promotion Intelligence Packet 06

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Research / Promotion Intelligence`
Packet: `06`
Status: `defined`

## Goal

Persist deterministic review outcomes as governed state transitions.

## Invariant

`/research-factory/intelligence/persisted-governed-state-transitions/latest` must return one deterministic governed transition per resolved review outcome and persist the transition into the governed alpha state surfaces.

## Acceptance

The packet is acceptable when:

- the surface returns `prior_governed_state`, `new_governed_state`, `transition_timestamp`, `transition_source_packet`, and `authority_surface`
- `shadow` can persist to `shadow`
- `retire` can persist to `retired`
- `needs_more_evidence` can persist without ambiguous state change
- the transition is appended to `alpha_status_events`
- the surface exposes a `transition_summary`
- a verifier can confirm representative transitions and persisted latest alpha state

## Route

- `GET /research-factory/intelligence/persisted-governed-state-transitions/latest`
