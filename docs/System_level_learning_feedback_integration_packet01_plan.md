# System-Level Learning / Feedback Integration Packet 01

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System-Level Learning / Feedback Integration`
Packet: `01`
Status: `defined`

## Goal

Create the first explicit cross-layer learning surface.

## Invariant

`/system/learning-feedback/latest` must expose one deterministic feedback bundle that connects:

- `PI-05 allocation outcome effectiveness`
- `ASI-05 effective selection slate`
- `RPI-06 persisted governed state transitions`

and resolves them into one family-level `learning_action`.

## Acceptance

The packet is acceptable when:

- the surface returns `run_id`, `cycle_id`, `mode`, and `cross_layer_coherence`
- the surface exposes `source_packets`
- each family item includes `portfolio_feedback`, `selection_feedback`, and `governed_transition_feedback`
- each family item resolves to one deterministic `learning_action`
- the allowed learning actions are `reinforce`, `caution`, `rebalance`, or `observe`
- the surface returns a system-level `feedback_summary.system_learning_action`
- a verifier can confirm representative family outcomes and coherence

## Route

- `GET /system/learning-feedback/latest`
