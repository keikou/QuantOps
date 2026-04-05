# Data Schema

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_data_schema_summary`

## Purpose

This file summarizes the schema-like data nouns that repeatedly appear across the current system contracts.

## Current Schema Families

### Summary Display Fields

- `stable_value`
- `live_delta`
- `display_value`
- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

### State And Lineage Fields

- `*_state`
- `*_state_id`
- `previous_*_state_id`
- `generated_at`
- `last_*_tick`
- `stale_flag`

### Decision And Action Fields

- `*_decision`
- `*_action`
- `system_*_action`
- `approval_status`
- `deployment_action`
- `flow_action`

### Effectiveness Fields

- `beneficial`
- `neutral`
- `adverse`
- `realized_effect`
- `consumed_effect`
- `utilization_ratio`

## Schema Rule

- names should describe the role, not just the source
- operator-visible fields should prefer explicit nouns over overloaded generic names
- new lane surfaces should follow existing state / decision / consumption / effectiveness naming where possible

## Read Next

1. `./api-summary-contracts.md`
2. `./runtime_checkpoint_shapes.md`
3. `./endpoint_contract_matrix.md`
