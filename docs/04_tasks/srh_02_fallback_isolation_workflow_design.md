# SRH-02 Fallback Isolation Workflow Design

## Purpose

When a dependency circuit opens, SRH-02 prevents the failure from spreading by routing to a fallback dependency or isolating the failed dependency.

## Workflow

```text
1. dependency failure is recorded
2. circuit breaker evaluates failure count
3. circuit opens
4. fallback selector checks fallback_dependency_id
5. fallback route is persisted or isolation event is created
6. operator-visible latest endpoints expose the result
```

## Fallback Route

Fallback routes are persisted in `runtime_fallback_routes` with `route_status = ACTIVE`.

## Isolation Event

If no fallback exists, SRH-02 persists `ISOLATED` in `runtime_dependency_events`.

## Integration Boundary

SRH-02 may read SRH-01 runtime health context but does not re-score runtime health and does not mutate governance or audit evidence.
