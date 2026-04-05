# Data Flow

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `current_data_flow_summary`

## Purpose

This file describes the current high-level movement of truth from runtime generation to operator-visible consumption.

## Flow

1. `V12` produces runtime truth, snapshots, and lower-level summaries
2. read-model and summary surfaces stabilize that truth for downstream use
3. `QuantOps API` consumes upstream truth and emits operator-facing contracts
4. checkpoint lanes expose system surfaces under `/system/*`
5. `frontend` consumes stable contracts and renders operator-visible state

## Docs Flow

1. `00_index` routes the reader
2. `03_plans/current.md` names the active lane
3. `04_tasks/current.md` names the active executable task
4. supporting docs refine scope
5. code inspection and verifiers confirm repo truth
6. canonical docs receive writeback

## Failure Interpretation Rule

When data appears inconsistent, prefer checking:

1. contract docs
2. runtime and route-local evidence
3. the narrowest verifier

Only after that should the issue be treated as architectural drift rather than local implementation or docs-state noise.
