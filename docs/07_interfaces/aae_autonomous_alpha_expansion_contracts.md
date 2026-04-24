# Autonomous Alpha Expansion Contracts

Date: `2026-04-24`
Repo: `QuantOps_github`
Status: `aae01_initial_contracts`

## Canonical AAE Surfaces

1. `GET /system/alpha-discovery-candidates/latest`
2. `GET /system/alpha-validation-results/latest`
3. `GET /system/alpha-admission-decision/latest`
4. `GET /system/alpha-lifecycle-state/latest`
5. `GET /system/alpha-inventory-health/latest`

## Contract Intent

The AAE family answers one invariant:

```text
the strategy universe must expand with newly discovered candidates that survive validation under the current or emerging regime
```

## Discovery

`GET /system/alpha-discovery-candidates/latest` returns discovery queue state.

Primary fields:

- `candidate_state`
- `validation_decision`
- `family_regime_state`
- `discovery_priority`
- `discovery_action`

## Validation

`GET /system/alpha-validation-results/latest` returns the latest alpha-level validation truth.

Primary fields:

- `validation_status`
- `validation_decision`
- `summary_score`
- `validation_source`
- `validation_action`

## Admission

`GET /system/alpha-admission-decision/latest` returns the deterministic admission posture.

Primary fields:

- `rank_score`
- `alpha_admission_decision`
- `admission_reason`
- `current_lifecycle_state`

## Lifecycle

`GET /system/alpha-lifecycle-state/latest` returns the currently visible alpha lifecycle stage.

Primary fields:

- `current_lifecycle_state`
- `lifecycle_stage`
- `latest_event_type`
- `latest_admission_decision`

## Inventory Health

`GET /system/alpha-inventory-health/latest` returns whether the alpha pipeline is healthy enough to replace dead inventory.

Primary fields:

- `health_status`
- `replacement_pressure`
- `candidate_count`
- `validated_count`
- `admit_count`
- `live_inventory_count`
- `system_inventory_action`
