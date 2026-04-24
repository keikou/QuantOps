# Autonomous Alpha Expansion / Strategy Generation Intelligence Packet 03 Plan

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Autonomous Alpha Expansion / Strategy Generation Intelligence`
Packet: `AAE-03`
Status: `implemented_runtime_expansion_loop`

## Packet Name

`AAE-03: Runtime Deployment, Feedback, And Winner Control`

## Purpose

`AAE-02` made generation and replacement deterministic.

The next requirement is:

- expose which replacement candidates are runtime-deployable
- expose live review and decay feedback for runtime alpha candidates
- expose rollback response and runtime winner selection
- expose whether runtime alpha expansion is actually healthy

## Required System Surfaces

1. `GET /system/alpha-runtime-deployment-candidates/latest`
2. `GET /system/alpha-runtime-governance-feedback/latest`
3. `GET /system/alpha-runtime-rollback-response/latest`
4. `GET /system/alpha-runtime-champion-challenger/latest`
5. `GET /system/alpha-runtime-expansion-effectiveness/latest`

## Runtime Deployment Contract

`GET /system/alpha-runtime-deployment-candidates/latest` must expose:

- `alpha_id`
- `model_id`
- `deployment_candidate_status`
- `recommended_rollout_stage`
- `runtime_deployment_action`

## Runtime Feedback Contract

`GET /system/alpha-runtime-governance-feedback/latest` must expose:

- `alpha_id`
- `live_review_decision`
- `alpha_decay_severity`
- `runtime_feedback_status`
- `runtime_feedback_action`

## Runtime Rollback Contract

`GET /system/alpha-runtime-rollback-response/latest` must expose:

- `alpha_id`
- `runtime_rollback_response`
- `runtime_rollback_reason`
- `selected_model_id`

## Runtime Competition Contract

`GET /system/alpha-runtime-champion-challenger/latest` must expose:

- `alpha_id`
- `runtime_competition_role`
- `winner`
- `recommended_action`
- `runtime_competition_action`

## Runtime Effectiveness Contract

`GET /system/alpha-runtime-expansion-effectiveness/latest` must expose:

- `effectiveness_status`
- `deployment_ready_count`
- `healthy_runtime_count`
- `rollback_runtime_count`
- `switch_runtime_count`
- `system_alpha_runtime_expansion_action`

## Dependency Boundary

`AAE-03` should build on:

- `AAE-02`
- `DRI-05`
- `RPI-06`

## Verification

Use:

- `test_bundle/scripts/verify_autonomous_alpha_expansion_strategy_generation_intelligence_packet03.py`
