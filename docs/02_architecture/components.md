# Components

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `current_component_map`

## Purpose

This file names the main component groups so a reader can place implementation work before reading the detailed masters.

## Main Components

### `apps/v12-api`

- runtime truth producers
- execution, portfolio, and intelligence input surfaces
- lower-level truth and writer behavior

### `apps/quantops-api`

- contract translation
- aggregated read surfaces
- lane checkpoint APIs such as rollout, capital control, and meta-portfolio outputs

### `apps/quantops-frontend`

- operator-facing presentation
- stable/live read composition
- workflow-visible display of current contracts

## Supporting Documentation Components

- `docs/07_interfaces/` defines the API and payload view
- `docs/09_runtime_ops/` defines runtime investigation and operational handling
- `docs/10_agent/` defines the docs-first operating loop for AI execution

## Rule

If a task changes one component's responsibility boundary, update the nearby architecture and interface docs before treating the new boundary as canonical.
