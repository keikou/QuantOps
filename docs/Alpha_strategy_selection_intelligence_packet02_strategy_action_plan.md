# Alpha / Strategy Selection Intelligence Packet 02

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha / Strategy Selection Intelligence`
Packet: `02`
Status: `defined`

## Goal

Turn `ASI-01` selection output into one explicit upstream strategy action per alpha.

## Invariant

`/alpha/intelligence/strategy-actions/latest` must resolve each alpha into exactly one deterministic `resolved_strategy_action`.

## Acceptance

The packet is acceptable when:

- the surface returns `selection_action`, `selection_score`, `resolved_strategy_action`, `strategy_action_rationale`, and `review_priority`
- `resolved_strategy_action` is one of `promote / shadow / research / defer`
- `global_guard_halt` forces `defer`
- high-quality selections can resolve to `promote`
- viable but not promotion-ready selections resolve to `shadow`
- lower-quality or constrained selections resolve to `research` or `defer`

## Route

- `GET /alpha/intelligence/strategy-actions/latest`
