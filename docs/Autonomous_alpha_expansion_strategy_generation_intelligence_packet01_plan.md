# Autonomous Alpha Expansion / Strategy Generation Intelligence Packet 01 Plan

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Autonomous Alpha Expansion / Strategy Generation Intelligence`
Packet: `AAE-01`
Status: `implemented_initial_loop`

## Packet Name

`AAE-01: Alpha Discovery & Validation Loop`

## Purpose

The completed system can now gate, allocate, deploy, and retire strategy families.

The next requirement is different:

- dead alpha must be replaced by newly discovered alpha
- candidate alpha must be validated under the current or emerging regime
- admission into live inventory must become explicit instead of implicit

## Required System Surfaces

`AAE-01` should make the following operator-visible surfaces explicit:

1. `GET /system/alpha-discovery-candidates/latest`
2. `GET /system/alpha-validation-results/latest`
3. `GET /system/alpha-admission-decision/latest`
4. `GET /system/alpha-lifecycle-state/latest`
5. `GET /system/alpha-inventory-health/latest`

## Discovery Contract

`GET /system/alpha-discovery-candidates/latest` must expose:

- `alpha_id`
- `alpha_family`
- `candidate_state`
- `validation_decision`
- `family_regime_state`
- `discovery_priority`
- `discovery_action`

## Validation Contract

`GET /system/alpha-validation-results/latest` must expose:

- `alpha_id`
- `validation_status`
- `validation_decision`
- `summary_score`
- `validation_source`
- `validation_action`

## Admission Contract

`GET /system/alpha-admission-decision/latest` must expose:

- `alpha_id`
- `rank_score`
- `alpha_admission_decision`
- `admission_reason`
- `current_lifecycle_state`

## Lifecycle Contract

`GET /system/alpha-lifecycle-state/latest` must expose:

- `alpha_id`
- `current_lifecycle_state`
- `lifecycle_stage`
- `latest_event_type`
- `latest_admission_decision`

## Inventory Health Contract

`GET /system/alpha-inventory-health/latest` must expose:

- `health_status`
- `replacement_pressure`
- `candidate_count`
- `validated_count`
- `admit_count`
- `live_inventory_count`
- `system_inventory_action`

## Dependency Boundary

`AAE-01` should build on already completed checkpoints and not reopen them:

- `ASI-05`
- `RPI-06`
- `SERI-05`

## Verification

Use:

- `test_bundle/scripts/verify_autonomous_alpha_expansion_strategy_generation_intelligence_packet01.py`

Expected shape:

- `status = ok`
- `failures = []`
