# Alpha Evaluation / Selection Intelligence Packet 08 Plan

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-08: Self-Improving Alpha Loop`
Status: `implemented`

## Purpose

`AES-08` closes the loop across `ASD`, `AAE`, `AES`, portfolio, and execution feedback.

It answers:

- which alpha structures and families survived live deployment
- what learning signals should feed generation and evaluation policy
- what bounded policy recommendations should be surfaced without silently rewriting production logic

## Core Invariant

```text
The alpha factory must improve from realized evidence without overfitting to recent noise.
```

## Canonical Surfaces

- `POST /system/alpha-feedback-loop/run`
- `GET /system/alpha-feedback-loop/latest`
- `GET /system/alpha-learning-signals/latest`
- `GET /system/alpha-generation-priors/latest`
- `GET /system/alpha-family-performance/latest`
- `GET /system/alpha-policy-recommendations/latest`
- `GET /system/alpha-feedback-loop/alpha/{alpha_id}`
- `GET /system/alpha-feedback-loop/family/{family_id}`
- `POST /system/alpha-policy-recommendations/apply`

## Implementation Boundary

`AES-08` consumes `AES-07` retirement and live-health evidence. It does not mutate generator, evaluation, or portfolio policy directly.

It produces:

- alpha outcome class
- structural motif signal
- metric predictiveness signal
- generation prior recommendation
- family performance recommendation
- operator-controlled policy application record

## Storage

- `alpha_feedback_runs`
- `alpha_realized_outcomes`
- `alpha_structural_motifs`
- `alpha_metric_predictiveness`
- `alpha_generation_priors`
- `alpha_family_performance`
- `alpha_policy_recommendations`
- `alpha_policy_applications`

## Definition Of Done

- feedback loop run materializes from latest retirement decisions
- realized outcomes and learning signals are operator-visible
- generation priors and family performance are queryable
- policy recommendations are bounded and approval-gated
- per-alpha and per-family feedback lookups are queryable
- docs and contract inventories include AES-08 surfaces

