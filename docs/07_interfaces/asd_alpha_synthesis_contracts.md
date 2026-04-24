# Alpha Synthesis / Structural Discovery Contracts

Date: `2026-04-24`
Repo: `QuantOps_github`
Status: `asd01_initial_contracts`

## Canonical ASD Surfaces

1. `GET /system/alpha-synthesis-candidates/latest`
2. `GET /system/alpha-structure-search-state/latest`
3. `GET /system/alpha-novelty-evaluation/latest`
4. `GET /system/alpha-expression-library/latest`
5. `GET /system/alpha-synthesis-effectiveness/latest`

## Contract Intent

The `ASD` family answers one invariant:

```text
the system must be able to generate symbolic alpha structures
not explicitly predefined in the existing template space
```

## Expected Contract Progression

1. generated symbolic alpha candidates
2. current structure search state
3. novelty scoring against the expression library
4. persisted expression library state
5. symbolic synthesis effectiveness
