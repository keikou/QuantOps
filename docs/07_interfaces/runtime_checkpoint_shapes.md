# Runtime Checkpoint Shapes

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_runtime_checkpoint_shapes`

## Purpose

This file summarizes the recurring checkpoint-visible shape used by the current intelligence lanes.

## Common Checkpoint Pattern

The current lanes tend to expose five related surfaces:

1. latest decision or allocation view
2. explicit decision or docket view
3. persisted state view
4. applied or consumed view
5. effectiveness or outcome view

## Current Lane Shape Examples

- `Deployment / Rollout Intelligence`
  - decision
  - candidate docket
  - rollout state
  - rollout consumption
  - rollout effectiveness
- `Live Capital Control`
  - live capital control
  - adjustment decision
  - control state
  - control consumption
  - control effectiveness
- `Meta Portfolio Intelligence`
  - allocation
  - decision
  - state
  - flow
  - efficiency

## Contract Rule

- persisted-state surfaces should expose an id and previous-id linkage when possible
- applied or consumed surfaces should make the realized downstream effect explicit
- effectiveness surfaces should collapse the outcome into one deterministic classification such as `beneficial`, `neutral`, or `adverse`

## Use

Use this file when designing the next checkpoint lane so new surfaces match the existing operator and AI expectations.
