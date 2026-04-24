# AES-08 Self-Improving Alpha Loop

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-08`
Status: `draft`

## Purpose

`AES-08` defines the closed-loop learning layer across `ASD`, `AAE`, `AES`, portfolio, and execution feedback.

It answers:

- which alpha structures, families, and metrics actually survive live deployment
- what bounded policy recommendations should be made back into generation, evaluation, and lifecycle control
- how the alpha factory should improve without silently rewriting production logic

## Core Invariant

```text
The alpha factory must improve from realized evidence without overfitting to recent noise.
```

## Canonical Surfaces

1. `POST /system/alpha-feedback-loop/run`
2. `GET /system/alpha-feedback-loop/latest`
3. `GET /system/alpha-learning-signals/latest`
4. `GET /system/alpha-generation-priors/latest`
5. `GET /system/alpha-family-performance/latest`
6. `GET /system/alpha-policy-recommendations/latest`
7. `GET /system/alpha-feedback-loop/alpha/{alpha_id}`
8. `GET /system/alpha-feedback-loop/family/{family_id}`
9. `POST /system/alpha-policy-recommendations/apply`

## Main Outputs

- alpha outcome classes
- structural motif learning
- metric predictiveness analysis
- threshold calibration recommendations
- generation prior updates
- family performance recommendations
- operator-approved policy application flow

## Data Model Draft

- `alpha_feedback_runs`
- `alpha_realized_outcomes`
- `alpha_structural_motifs`
- `alpha_metric_predictiveness`
- `alpha_generation_priors`
- `alpha_family_performance`
- `alpha_policy_recommendations`

## Completion Meaning

If `AES-08` reaches checkpoint-complete, `AES v1` closes the loop from:

- evaluate
- validate
- ensemble
- explain
- capacity-check
- dynamically weight
- retire
- learn
