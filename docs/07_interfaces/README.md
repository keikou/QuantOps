# Interfaces Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `initial_interfaces_index`

## Purpose

This folder is the canonical entrypoint for API, schema, contract, and display-interface documentation.

At the current repo stage, the interface truth is still split across a few older docs.
This index tells humans and AI agents which contract docs to trust first.

## Current Canonical Interface Docs

1. `./current_contracts.md`
2. `./api-summary-contracts.md`
3. `./portfolio-display-semantics.md`
4. `../02_architecture/architecture-read-models.md`
5. `./V12_QuantOps_Interface_Contract.md`
6. `./event_contracts.md`
7. `./runtime_checkpoint_shapes.md`
8. `./operator_bundle_payloads.md`
9. `./endpoint_contract_matrix.md`
10. `./lane_surface_inventory.md`
11. `./api_endpoints.md`
12. `./data_schema.md`
13. `./runtime_payloads.md`

## What Counts As An Interface Here

In this repo, `interfaces` includes:

- API response contracts
- summary/display semantics
- read-model contracts
- event and checkpoint payload shapes
- freshness/build metadata semantics

It is broader than just endpoint lists.

## Current Highest-Signal Contracts

- summary/display contract:
  - `stable_value`
  - `live_delta`
  - `display_value`
- freshness/build metadata:
  - `build_status`
  - `source_snapshot_time`
  - `rebuilt_at`
  - `data_freshness_sec`
- portfolio display semantics:
  - truth rows vs display rows
  - net signed quantity semantics
  - aggregated margin/exposure display basis
- read-model separation:
  - truth layer
  - read-model/summary layer
  - QuantOps aggregation layer
  - frontend presentation layer

## Next Interface Gaps

The current gaps are:

- regime-adaptation lane contracts are not documented yet
- request-body schema depth is still thin
- family-level payload lineage is still summarized rather than fully enumerated

## Recommended Next Additions

1. add `SERI` family surfaces when packet 01 starts
2. deepen `event_contracts.md`
3. deepen `runtime_checkpoint_shapes.md`
4. deepen `operator_bundle_payloads.md`
5. deepen `endpoint_contract_matrix.md`
6. deepen `api_endpoints.md`
7. deepen `data_schema.md`
8. deepen `runtime_payloads.md`

## Rule

When a response or UI field is ambiguous, prefer adding an interface contract doc instead of letting the meaning live only in code or thread memory.
