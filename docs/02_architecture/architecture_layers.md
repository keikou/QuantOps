# Architecture Layers

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `current_architecture_layer_map`

## Purpose

This file is the short layer map for the current system.

Use it before the larger master docs when you need a fast answer to:

- which layer owns truth
- which layer owns contracts
- which layer owns presentation

## Current Layer Stack

1. `V12 truth/runtime layer`
   - correctness-first state
   - runtime snapshots
   - execution and portfolio truth
2. `V12 read-model / summary layer`
   - cheap stable reads
   - summary routes for operator and API consumption
3. `QuantOps aggregation / contract layer`
   - contract-first translation
   - operator-facing summaries
   - lane checkpoint surfaces
4. `frontend presentation layer`
   - stable summary display
   - live-feed presentation
   - operator workflow UI

## Current Architectural Rule

- truth should not be redefined in the frontend
- read models should not silently become the new truth
- contract layers should make display semantics explicit
- presentation should not merge stable and live values without a documented contract

## Read Next

1. `./current_architecture.md`
2. `./V12_Architecture_Master.md`
3. `./QuantOps_Architecture_Master.md`
4. `./architecture-read-models.md`
