# System Overview

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `current_system_overview`

## Purpose

This file gives the shortest architecture overview for a reader who needs the current system shape before opening the larger master documents.

## Core Shape

The repo operates as a three-system stack:

1. `V12` produces correctness-first runtime truth
2. `QuantOps API` translates that truth into operator-facing contracts
3. `frontend` renders stable summaries and live operational views

## Current Control Logic

- completed checkpoint lanes publish system-facing surfaces through the API layer
- docs are the current operating system for deciding what lane and task are active
- verifiers are the first mechanism for deciding whether repo truth has actually changed

## Read Next

1. `./architecture_layers.md`
2. `./system_ownership_map.md`
3. `./components.md`
4. `./data_flow.md`
