# SRH-02 Circuit Breaker State Machine Design

## States

- `CLOSED`
- `OPEN`
- `HALF_OPEN`

## Allowed Transitions

```text
CLOSED -> OPEN
OPEN -> HALF_OPEN
HALF_OPEN -> CLOSED
HALF_OPEN -> OPEN
OPEN -> CLOSED
```

## Blocked Transition

```text
CLOSED -> HALF_OPEN
```

`HALF_OPEN` requires an existing open circuit. Blocked transitions are persisted to `runtime_circuit_transitions` with `allowed = false`.

## Failure Rule

Repeated failures increment `failure_count`. When `failure_count >= threshold`, the circuit opens and fallback or isolation is selected.

## Recovery Rule

Successful recovery probe closes the circuit. Failed recovery probe reopens it.
