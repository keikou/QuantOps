# Operator Bundle Payloads

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_operator_bundle_payload_reference`

## Purpose

This file summarizes the operator-facing payload bundles already present in the repo.

## Current Operator-Facing Bundles

- `GET /system/operator-diagnostic-bundle`
- `GET /system/recovery-replay-diagnostic-bundle`
- `GET /system/hardening-architect-handoff/latest`
- `GET /system/resume-operator-packet/latest`

## Current Bundle Contract Expectations

- a bundle should answer one operator question directly
- a bundle should prefer explicit sections over mixed free-form text
- a bundle should preserve source or lineage hints when the payload is stitched from multiple surfaces
- a bundle should not require the operator to infer the next action from scattered fields

## Current Common Fields

- `status`
- `generated_at` or equivalent timestamp
- summary or action fields
- nested sections or items for drilldown

## Rule

If a new operator-facing endpoint is introduced, add it here once the payload becomes part of the expected operator workflow.
