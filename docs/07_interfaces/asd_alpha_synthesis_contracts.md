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

## ASD-02 Extension

The next `ASD` family extends from random symbolic generation into evolutionary search:

1. `GET /system/alpha-parent-candidates/latest`
2. `GET /system/alpha-mutation-candidates/latest`
3. `GET /system/alpha-crossover-candidates/latest`
4. `GET /system/alpha-evolution-search-state/latest`
5. `GET /system/alpha-evolution-effectiveness/latest`

## ASD-03 Extension

The next `ASD` family extends from evolutionary search into regime-conditioned synthesis:

1. `GET /system/alpha-regime-synthesis-agenda/latest`
2. `GET /system/alpha-regime-targeted-candidates/latest`
3. `GET /system/alpha-regime-fit-evaluation/latest`
4. `GET /system/alpha-regime-expression-map/latest`
5. `GET /system/alpha-regime-synthesis-effectiveness/latest`

## ASD-04 Extension

The next `ASD` family extends from regime-conditioned synthesis into deterministic LLM-assisted hypothesis generation:

1. `GET /system/alpha-hypothesis-agenda/latest`
2. `GET /system/alpha-llm-hypothesis-prompts/latest`
3. `GET /system/alpha-llm-translation-candidates/latest`
4. `GET /system/alpha-hypothesis-critique/latest`
5. `GET /system/alpha-hypothesis-effectiveness/latest`

## ASD-05 Extension

The next `ASD` family extends from hypothesis generation into feedback optimization:

1. `GET /system/alpha-hypothesis-feedback-queue/latest`
2. `GET /system/alpha-hypothesis-prompt-tuning/latest`
3. `GET /system/alpha-synthesis-policy-updates/latest`
4. `GET /system/alpha-feedback-learning-state/latest`
5. `GET /system/alpha-feedback-optimization-effectiveness/latest`
