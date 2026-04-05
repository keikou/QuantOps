# Current Architecture

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `current_architecture_summary`

## Purpose

This file is the short human/AI summary of the current architecture set.

Use it first when you need to answer:

- what the control plane is
- how V12 and QuantOps divide responsibilities
- where read models and writer observability fit

## Canonical Docs

1. `./system_overview.md`
2. `./architecture_layers.md`
3. `./system_ownership_map.md`
4. `./components.md`
5. `./data_flow.md`
6. `./QuantOps_Architecture_Master.md`
7. `./V12_Architecture_Master.md`
8. `../07_interfaces/V12_QuantOps_Interface_Contract.md`
9. `./architecture-read-models.md`
10. `./writer-observability.md`

## Summary

- `QuantOps` is the control plane and operator workspace
- `V12` is the trading engine and runtime truth producer
- `QuantOps API` is the contract and aggregation layer between runtime truth and operator-facing surfaces
- read models exist to create stable, presentation-oriented views of truth
- writer observability exists to explain freshness, lag, and degraded write paths
- ownership boundaries matter as much as code structure

## Investigation Order

1. `system_overview.md`
2. `architecture_layers.md`
3. `system_ownership_map.md`
4. `components.md`
5. `data_flow.md`
6. `QuantOps_Architecture_Master.md`
7. `V12_Architecture_Master.md`
8. `V12_QuantOps_Interface_Contract.md`
9. `architecture-read-models.md`
10. `writer-observability.md`
