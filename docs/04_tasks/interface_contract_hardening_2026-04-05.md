# Task: Interface Contract Hardening

Date: `2026-04-05`
Status: `active`

## Goal

Strengthen `07_interfaces/` so humans and AI can inspect the current contract surface without reverse-engineering endpoints from code.

## Why Now

The docs structure is now mostly in place, and the latest docs review identified `interfaces` as the weakest high-value layer.

## Inputs

- `../07_interfaces/README.md`
- `../07_interfaces/current_contracts.md`
- `../08_dev_guides/current_dev_guide.md`
- `../../apps/v12-api/ai_hedge_bot/api/routes/system.py`

## Steps

1. add the missing interface contract docs called out by the interface index
2. align the interface index and contract summary with those new docs
3. keep the new docs compact and routing-oriented rather than duplicating code

## Outputs

- `docs/07_interfaces/event_contracts.md`
- `docs/07_interfaces/runtime_checkpoint_shapes.md`
- `docs/07_interfaces/operator_bundle_payloads.md`
- `docs/07_interfaces/endpoint_contract_matrix.md`

## Non-Goals

- rewriting every payload schema in exhaustive detail
- moving every root-level doc physically in the same step
- changing runtime behavior

## Completion Check

- the interface index points to the missing contract docs explicitly
- the current contract summary routes readers into the new docs
- the docs layer reduces the need to inspect `system.py` just to find the current contract surfaces
