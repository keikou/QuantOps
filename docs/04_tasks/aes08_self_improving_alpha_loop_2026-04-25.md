# AES-08 Self-Improving Alpha Loop Task

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-08`
Status: `implemented`

## Active Boundary

Implement closed-loop alpha learning after `AES-07`.

## Required Surfaces

- `POST /system/alpha-feedback-loop/run`
- `GET /system/alpha-feedback-loop/latest`
- `GET /system/alpha-learning-signals/latest`
- `GET /system/alpha-generation-priors/latest`
- `GET /system/alpha-family-performance/latest`
- `GET /system/alpha-policy-recommendations/latest`
- `GET /system/alpha-feedback-loop/alpha/{alpha_id}`
- `GET /system/alpha-feedback-loop/family/{family_id}`
- `POST /system/alpha-policy-recommendations/apply`

## Non-Goals

- do not silently rewrite ASD generation policy
- do not silently rewrite AES thresholds
- do not replace AAE lifecycle control
- do not execute portfolio changes
- do not replay completed AES-01 through AES-07 packets

## Completion Evidence

- `alpha_feedback` package exists
- runtime tables exist for outcomes, motifs, metrics, priors, family performance, policy recommendations, and policy applications
- `/system/*` routes expose feedback loop, learning signal, prior, family, and policy recommendation surfaces
- verifier checks the plan and task surfaces

