# Alpha Evaluation / Selection Contracts

Date: `2026-04-25`
Repo: `QuantOps_github`
Status: `aes03_extended_contracts`

## Canonical AES Surfaces

1. `GET /system/alpha-evaluation/latest`
2. `GET /system/alpha-decay-analysis/latest`
3. `GET /system/alpha-correlation-matrix/latest`
4. `GET /system/alpha-robustness-ranking/latest`
5. `GET /system/alpha-selection-decisions/latest`
6. `POST /system/alpha-evaluation/run`
7. `GET /system/alpha-evaluation/candidate/{alpha_id}`

## Contract Intent

The `AES` family answers one invariant:

```text
the system must reliably distinguish real alpha from noise
before promotion into the live strategy pool
```

## Expected Contract Progression

1. evaluation summary
2. decay analysis
3. correlation and redundancy view
4. robustness ranking
5. selection decision
6. explicit evaluation run trigger
7. per-candidate evaluation lookup

## AES-02 Extension

The next `AES` family extends from evaluation into walk-forward and out-of-sample validation:

1. `POST /system/alpha-walk-forward/run`
2. `GET /system/alpha-walk-forward/latest`
3. `GET /system/alpha-walk-forward/candidate/{alpha_id}`
4. `GET /system/alpha-oos-validation/latest`
5. `GET /system/alpha-validation-decisions/latest`
6. `GET /system/alpha-validation-failures/latest`

## AES-03 Extension

The next `AES` family extends from alpha-level validation into portfolio-ready ensemble construction:

1. `POST /system/alpha-ensemble/run`
2. `GET /system/alpha-ensemble/latest`
3. `GET /system/alpha-ensemble/candidates/latest`
4. `GET /system/alpha-ensemble/candidate/{ensemble_id}`
5. `GET /system/alpha-ensemble-correlation/latest`
6. `GET /system/alpha-marginal-contribution/latest`
7. `GET /system/alpha-ensemble-selection/latest`
8. `GET /system/alpha-ensemble-weights/latest`

## AES-04 Extension

The next `AES` family extends from ensemble construction into economic meaning and factor attribution:

1. `POST /system/alpha-factor-attribution/run`
2. `GET /system/alpha-factor-attribution/latest`
3. `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
4. `GET /system/alpha-factor-exposure/latest`
5. `GET /system/alpha-residual-alpha/latest`
6. `GET /system/alpha-economic-risk/latest`
7. `GET /system/alpha-factor-concentration/latest`
8. `GET /system/alpha-economic-meaning/latest`
9. `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`
