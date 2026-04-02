# System-Level Learning / Feedback Integration Packet 02

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System-Level Learning / Feedback Integration`
Packet: `02`
Status: `defined`

## Goal

Convert cross-layer learning feedback into next-cycle policy updates.

## Invariant

`/system/learning-policy-updates/latest` must transform `Packet 01` family-level `learning_action` into one deterministic next-cycle policy update per family.

## Acceptance

The packet is acceptable when:

- the surface returns `run_id`, `cycle_id`, `mode`, and `cross_layer_coherence`
- each family item includes `selection_score_adjustment`, `capital_multiplier_adjustment`, `review_pressure`, and `runtime_caution`
- `reinforce`, `caution`, `rebalance`, and `observe` map to deterministic update values
- the surface returns `policy_update_summary.system_policy_action`
- a verifier can confirm representative family updates and coherence

## Route

- `GET /system/learning-policy-updates/latest`
