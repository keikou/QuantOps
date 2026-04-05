# Task: Docs Route Sync

Date: `2026-04-06`
Status: `reusable`

## Goal

Bring canonical docs routes back in sync when folder entrypoints, migration maps, or current-state docs drift apart.

## Why Now

The repo now depends on a docs-first operating model, so stale routing breaks both human onboarding and AI execution.

## Inputs

- `../00_index/README.md`
- `../00_index/current_docs_migration_map.md`
- the closest folder `README.md` or `current.md`
- the narrowest relevant docs verifier

## Steps

1. identify the stale route or ownership mismatch
2. update the canonical entrypoint first
3. update the migration map or supporting index if the route changed
4. run the narrowest relevant docs verifier
5. write the resolved route back into the affected current-state doc if needed

## Outputs

- one corrected canonical route
- one verifier-backed sync result
- one concise writeback into the current docs surface when state changed

## Non-Goals

- mass physical file moves
- rewriting document content that is not part of the route mismatch
- reopening completed implementation lanes

## Completion Check

- the route is readable from the canonical index without thread memory
- the relevant docs verifier passes
