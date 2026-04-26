# SRH-02 Dependency Registry Design

## Purpose

The dependency registry defines the runtime systems that SRH-02 can isolate.

## Registry Fields

- `dependency_id`
- `dependency_type`
- `name`
- `owner`
- `criticality`
- `fallback_dependency_id`
- `metadata_json`
- `registered_at`
- `is_active`

## Supported Dependencies

- data feed
- execution venue
- broker or exchange adapter
- model service
- storage
- queue
- scheduler
- internal API
- external API

## Rules

- registration is append-only
- fallback is optional
- missing dependencies can be auto-registered for runtime observation
- frozen AFG tables are not mutated
