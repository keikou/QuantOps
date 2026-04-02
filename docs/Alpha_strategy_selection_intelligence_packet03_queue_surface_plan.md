# Alpha / Strategy Selection Intelligence Packet 03

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha / Strategy Selection Intelligence`
Packet: `03`
Status: `defined`

## Goal

Make the downstream queue destination for each alpha explicit after strategy-action resolution.

## Invariant

`/alpha/intelligence/selection-queues/latest` must map each alpha to exactly one queue.

## Acceptance

The packet is acceptable when:

- the surface returns `resolved_strategy_action`, `queue_name`, `queue_priority`, and `queue_reason`
- queue names are deterministic and come from `promotion_candidate / shadow_review / research_return / deferred_watchlist`
- `promote` maps to `promotion_candidate`
- `shadow` maps to `shadow_review`
- `research` maps to `research_return`
- `defer` maps to `deferred_watchlist`

## Route

- `GET /alpha/intelligence/selection-queues/latest`
