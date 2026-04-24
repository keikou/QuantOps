# Autonomous Alpha Expansion / Strategy Generation Intelligence Packet 02 Plan

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Autonomous Alpha Expansion / Strategy Generation Intelligence`
Packet: `AAE-02`
Status: `implemented_replacement_loop`

## Packet Name

`AAE-02: Alpha Generation Agenda & Replacement Loop`

## Purpose

`AAE-01` made discovery, validation, admission, lifecycle, and inventory health explicit.

The next requirement is:

- decide what the system should generate next
- decide which experiments should run next
- decide which validated candidates should replace fragile inventory
- make replacement state and effectiveness explicit

## Required System Surfaces

1. `GET /system/alpha-generation-agenda/latest`
2. `GET /system/alpha-experiment-docket/latest`
3. `GET /system/alpha-replacement-decision/latest`
4. `GET /system/alpha-replacement-state/latest`
5. `GET /system/alpha-expansion-effectiveness/latest`

## Generation Agenda Contract

`GET /system/alpha-generation-agenda/latest` must expose:

- `alpha_id`
- `alpha_family`
- `generation_priority`
- `generation_action`
- `replacement_pressure`

## Experiment Docket Contract

`GET /system/alpha-experiment-docket/latest` must expose:

- `alpha_id`
- `experiment_id`
- `experiment_status`
- `docket_state`
- `docket_action`

## Replacement Decision Contract

`GET /system/alpha-replacement-decision/latest` must expose:

- `alpha_id`
- `alpha_replacement_decision`
- `replacement_reason`
- `lifecycle_stage`
- `docket_state`

## Replacement State Contract

`GET /system/alpha-replacement-state/latest` must expose:

- `alpha_id`
- `replacement_state`
- `promotion_id`
- `demotion_id`
- `state_transition_note`

## Expansion Effectiveness Contract

`GET /system/alpha-expansion-effectiveness/latest` must expose:

- `expansion_status`
- `generation_ready_count`
- `replacement_ready_count`
- `active_replacement_count`
- `replacement_pressure`
- `system_alpha_expansion_action`

## Dependency Boundary

`AAE-02` should build on:

- `AAE-01`
- `RPI-06`
- `SERI-05`

## Verification

Use:

- `test_bundle/scripts/verify_autonomous_alpha_expansion_strategy_generation_intelligence_packet02.py`
