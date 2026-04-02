# System-Level Learning / Feedback Integration Packet 03

Date: `2026-04-02`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `System-Level Learning / Feedback Integration`
Packet: `03`
Status: `defined`

## Goal

Persist next-cycle learning policy state.

## Invariant

`/system/learning-policy-state/latest` must transform `Packet 02` policy updates into one persisted policy state per family.

## Acceptance

The packet is acceptable when:

- the surface returns `run_id`, `cycle_id`, `mode`, and `cross_layer_coherence`
- each family item includes `policy_state_id`, `applied_selection_score_adjustment`, `applied_capital_multiplier`, `applied_review_pressure`, and `applied_runtime_caution`
- the persisted row records `policy_source_packet`
- the surface returns `persisted_policy_state_summary.system_policy_state_action`
- a verifier can confirm representative persisted states and summary

## Route

- `GET /system/learning-policy-state/latest`
