# Event Contracts

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_event_contract_index`

## Purpose

This file defines the current event-like payload contract expectations used by runtime, checkpoint, and decision surfaces.

## Current Event Contract Rules

- every event-like payload should carry a top-level `status`
- every event-like payload should remain deterministic for the same underlying snapshot
- every event-like payload should expose a clear domain noun such as `families`, `items`, `docket`, `state`, or `flows`
- event-like payloads should prefer explicit action fields such as `system_*_action` over implied behavior

## Current Common Event Shape

```json
{
  "status": "ok",
  "generated_at": "2026-04-05T00:00:00Z",
  "system_action": "string",
  "items": []
}
```

## Current Event Families

- learning and policy surfaces
- deployment and rollout surfaces
- live capital control surfaces
- meta-portfolio surfaces
- future regime-adaptation surfaces

## Rule

If a payload is consumed as a state transition trigger or operator-visible decision bundle, document it here or in a dedicated payload-shape doc before extending it further.
