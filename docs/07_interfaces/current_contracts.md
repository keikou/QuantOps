# Current Interface Contracts

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_contract_summary`

## Purpose

This file is the short human/AI summary of the current contract surface.

Use it first when you need to answer:

- which values are stable vs live
- how the UI should interpret a value
- which contract doc to read next

## Contract Set 1: Summary Display Contract

Primary reference:

- `./api-summary-contracts.md`

Core fields:

- `stable_value`
- `live_delta`
- `display_value`
- `build_status`
- `source_snapshot_time`
- `rebuilt_at`
- `data_freshness_sec`

Meaning:

- `stable_value` is the stable summary baseline
- `live_delta` is the incremental overlay when explicitly provided
- `display_value` is what the UI should normally show
- freshness/build fields explain how trustworthy and recent the value is

## Contract Set 2: Portfolio Display Semantics

Primary reference:

- `./portfolio-display-semantics.md`

Core rules:

- truth rows and display rows are not the same thing
- normal portfolio display is symbol-aggregated
- quantity is net signed quantity
- display margin/exposure should align with the aggregated display basis
- lower-level V12 truth is preserved underneath

## Contract Set 3: Read-Model Separation

Primary reference:

- `../02_architecture/architecture-read-models.md`

Core rules:

- truth layer is authoritative
- read-model/summary layer is for cheap stable reads
- QuantOps aggregation layer translates upstream state for presentation
- frontend must keep stable summaries separate from live feeds unless the contract explicitly merges them

## Current UI/Operator Interpretation Rules

1. prefer `display_value` over recomputing values in the frontend
2. do not treat recent feeds as authoritative totals
3. inspect freshness/build metadata when a value looks wrong
4. treat display semantics as intentional, not as accounting truth replacement

## Current Canonical Path For Investigation

When an operator-facing value looks wrong, inspect in this order:

1. `display_value`
2. `stable_value`
3. `live_delta`
4. `build_status`
5. `source_snapshot_time`
6. `rebuilt_at`
7. `data_freshness_sec`

Then decide whether the problem is:

- stale data
- overlay confusion
- fallback/degraded path
- frontend merge mistake
- mismatch between truth view and display view

## Current Missing Interface Docs

- event contracts
- runtime checkpoint shapes
- operator bundle payload shapes
- acceptance result payload shapes

Current additions now available:

- `./event_contracts.md`
- `./runtime_checkpoint_shapes.md`
- `./operator_bundle_payloads.md`
- `./endpoint_contract_matrix.md`
- `./api_endpoints.md`
- `./data_schema.md`
- `./runtime_payloads.md`

## Current Recommendation

Until the interface layer is deeper, use this sequence:

1. `current_contracts.md`
2. `./api-summary-contracts.md`
3. `./portfolio-display-semantics.md`
4. `../02_architecture/architecture-read-models.md`
5. `./event_contracts.md`
6. `./runtime_checkpoint_shapes.md`
7. `./operator_bundle_payloads.md`
8. `./endpoint_contract_matrix.md`
9. `./api_endpoints.md`
10. `./data_schema.md`
11. `./runtime_payloads.md`
