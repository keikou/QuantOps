# System Ownership Map

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `current_system_ownership_map`

## Purpose

This file is the short ownership map for the current system architecture.

## Current Ownership

### `V12`

Owns:

- correctness-first runtime truth
- execution and portfolio snapshots
- writer cycles and runtime diagnostics
- base summary surfaces used as upstream truth inputs

Does not own:

- operator-facing aggregation contracts
- frontend display semantics

### `QuantOps API`

Owns:

- operator-facing contract translation
- read aggregation across upstream truth surfaces
- checkpoint and intelligence lane system surfaces
- stale/degraded/operator-visible semantics

Does not own:

- execution truth itself
- frontend rendering decisions

### `frontend`

Owns:

- operator workflow presentation
- stable summary and live feed rendering
- display composition under documented contracts

Does not own:

- backend truth semantics
- contract reinterpretation

## Rule

If a proposed change blurs these boundaries, document the boundary explicitly before implementing the change.
