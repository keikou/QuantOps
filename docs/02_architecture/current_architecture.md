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

1. `./QuantOps_Architecture_Master.md`
2. `./V12_Architecture_Master.md`
3. `../07_interfaces/V12_QuantOps_Interface_Contract.md`
4. `./architecture-read-models.md`
5. `./writer-observability.md`

## Summary

- `QuantOps` is the control plane and operator workspace
- `V12` is the trading engine and runtime truth producer
- read models exist to create stable, presentation-oriented views of truth
- writer observability exists to explain freshness, lag, and degraded write paths

## Investigation Order

1. `QuantOps_Architecture_Master.md`
2. `V12_Architecture_Master.md`
3. `V12_QuantOps_Interface_Contract.md`
4. `architecture-read-models.md`
5. `writer-observability.md`
