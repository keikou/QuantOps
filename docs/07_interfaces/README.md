# Interfaces Index

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `initial_interfaces_index`

## Purpose

This folder is the canonical entrypoint for API, schema, contract, and display-interface documentation.

At the current repo stage, the interface truth is still split across a few older root-level docs.
This index tells humans and AI agents which contract docs to trust first.

## Current Canonical Interface Docs

1. `./current_contracts.md`
2. `../api-summary-contracts.md`
3. `../portfolio-display-semantics.md`
4. `../architecture-read-models.md`

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

- no dedicated event contract doc
- no runtime checkpoint payload index
- no operator bundle payload reference
- no single endpoint contract matrix yet

## Recommended Next Additions

1. `event_contracts.md`
2. `runtime_checkpoint_shapes.md`
3. `operator_bundle_payloads.md`
4. `endpoint_contract_matrix.md`

## Rule

When a response or UI field is ambiguous, prefer adding an interface contract doc instead of letting the meaning live only in code or thread memory.
