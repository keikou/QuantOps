# Alpha / Strategy Selection Intelligence Packet 01

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha / Strategy Selection Intelligence`
Packet: `01`
Status: `defined`

## Goal

Start the next lane after `Portfolio Intelligence v1` by making alpha selection explicitly consume:

- alpha ranking quality
- execution sensitivity
- runtime control pressure
- portfolio tradeoff feedback
- realized allocation effectiveness

## Invariant

`/alpha/intelligence/selection/latest` must return one deterministic `selection_action` per alpha opportunity with explicit penalties and adjustments.

## Acceptance

The packet is acceptable when:

- the surface returns `alpha_id`, `base_rank_score`, `execution_penalty`, `control_penalty`, `portfolio_tradeoff_adjustment`, `portfolio_effectiveness_adjustment`, `selection_score`, and `selection_action`
- items are deterministically ordered by `selection_score`
- `selection_action` is one of `prioritize / hold / deprioritize / exclude`
- runtime control pressure is visible in `control_context`
- a verifier can seed portfolio/control evidence and confirm both positive and negative downstream adjustments are reflected in the selection output

## Inputs

- `/alpha/ranking`
- `Governance -> Runtime Control` checkpoint through `C6`
- `Portfolio Intelligence` checkpoint through `PI-05`

## Output

- plan doc
- verifier script
- `Alpha / Strategy Selection Intelligence` Packet 01 surface

## Route

- `GET /alpha/intelligence/selection/latest`
