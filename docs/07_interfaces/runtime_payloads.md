# Runtime Payloads

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_runtime_payload_summary`

## Purpose

This file summarizes the payload shapes most relevant to runtime, operator, and checkpoint-visible system surfaces.

## Current Runtime Payload Classes

### Health Payloads

Typical fields:

- `status`
- `mode`
- `symbols`
- `phase`
- `sprint`

### Bundle Payloads

Typical fields:

- `status`
- generated timestamp or equivalent
- summary fields
- nested sections for operator drilldown

### Lane Surface Payloads

Typical fields:

- top-level `status`
- family or item collection
- one explicit `system_*_action`
- ids or lineage fields for persisted-state views

### Consumption And Effectiveness Payloads

Typical fields:

- applied or consumed state/action fields
- realized or effective outcome fields
- one compact classification for next-step interpretation

## Current Runtime Payload Rule

Runtime-visible payloads should make the current action, current state, and current effect explicit enough for both operators and AI agents to act without re-deriving meaning from code.

## Read Next

1. `./operator_bundle_payloads.md`
2. `./runtime_checkpoint_shapes.md`
3. `./endpoint_contract_matrix.md`
4. `./seri_regime_adaptation_contracts.md`
