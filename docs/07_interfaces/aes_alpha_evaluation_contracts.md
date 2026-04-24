# Alpha Evaluation / Selection Contracts

Date: `2026-04-25`
Repo: `QuantOps_github`
Status: `aes08_extended_contracts`

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

## AES-05 Extension

The next `AES` family extends from attribution into capacity and crowding risk control:

1. `POST /system/alpha-capacity/run`
2. `GET /system/alpha-capacity/latest`
3. `GET /system/alpha-capacity/candidate/{alpha_id}`
4. `GET /system/alpha-crowding/latest`
5. `GET /system/alpha-impact/latest`
6. `GET /system/alpha-capacity/ensemble/{ensemble_id}`

## AES-06 Extension

The next `AES` family extends from capacity control into dynamic alpha weighting:

1. `POST /system/alpha-dynamic-weights/run`
2. `GET /system/alpha-dynamic-weights/latest`
3. `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}`
4. `GET /system/alpha-weight-adjustments/latest`
5. `GET /system/alpha-weight-drift/latest`
6. `GET /system/alpha-weight-constraints/latest`
7. `GET /system/alpha-weight-proposals/latest`

## AES-07 Extension

The next `AES` family extends from dynamic weighting into alpha kill switch and retirement control:

1. `POST /system/alpha-kill-switch/run`
2. `GET /system/alpha-kill-switch/latest`
3. `GET /system/alpha-kill-switch/alpha/{alpha_id}`
4. `GET /system/alpha-retirement/latest`
5. `GET /system/alpha-retirement/alpha/{alpha_id}`
6. `GET /system/alpha-deactivation-decisions/latest`
7. `GET /system/alpha-kill-switch-events/latest`
8. `POST /system/alpha-kill-switch/override`

## AES-08 Extension

The next `AES` family extends from retirement control into closed-loop alpha learning:

1. `POST /system/alpha-feedback-loop/run`
2. `GET /system/alpha-feedback-loop/latest`
3. `GET /system/alpha-learning-signals/latest`
4. `GET /system/alpha-generation-priors/latest`
5. `GET /system/alpha-family-performance/latest`
6. `GET /system/alpha-policy-recommendations/latest`
7. `GET /system/alpha-feedback-loop/alpha/{alpha_id}`
8. `GET /system/alpha-feedback-loop/family/{family_id}`
9. `POST /system/alpha-policy-recommendations/apply`
