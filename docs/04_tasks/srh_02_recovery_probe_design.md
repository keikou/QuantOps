# SRH-02 Recovery Probe Design

## Purpose

Recovery probes verify that an isolated dependency can safely return to service.

## Probe Lifecycle

```text
SCHEDULED
-> SUCCESS
or
-> FAILED
```

## Probe Rules

- schedule probe records the current circuit state
- successful probe closes the circuit
- failed probe opens or keeps open the circuit
- probe completion is append-only

## Evidence

Recovery probe rows are stored in `runtime_recovery_probes`. Circuit changes caused by probes are also stored in `runtime_circuit_breakers` and `runtime_circuit_transitions`.
