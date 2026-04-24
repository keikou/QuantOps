# AES-04 Economic Meaning / Factor Attribution Engine

Date: `2026-04-25`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Lane: `Alpha Evaluation / Selection Intelligence v1`
Packet: `AES-04`
Status: `draft`

## Purpose

`AES-04` defines the economic and factor attribution layer that sits after `AES-03`.

It answers:

- what market, style, and regime exposures each selected alpha carries
- how much return is factor-explained versus residual alpha
- whether ensemble concentration and hidden common drivers should limit production scaling

## Core Invariant

```text
The system must explain what economic or statistical drivers each alpha is exposed to before production scaling.
```

## Canonical Surfaces

1. `POST /system/alpha-factor-attribution/run`
2. `GET /system/alpha-factor-attribution/latest`
3. `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
4. `GET /system/alpha-factor-exposure/latest`
5. `GET /system/alpha-residual-alpha/latest`
6. `GET /system/alpha-economic-risk/latest`
7. `GET /system/alpha-factor-concentration/latest`
8. `GET /system/alpha-economic-meaning/latest`
9. `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`

## Main Outputs

- factor exposure table
- market beta estimate
- residual alpha score
- regime dependency profile
- hidden common driver flags
- production scaling recommendation

## Data Model Draft

- `alpha_attribution_runs`
- `alpha_factor_exposures`
- `alpha_factor_model_fit`
- `alpha_residual_alpha_scores`
- `alpha_regime_dependency`
- `alpha_factor_concentration`
- `alpha_hidden_driver_flags`
- `alpha_economic_meaning_labels`

## Integrations

- consumes `AES-03` selected ensemble and weights
- emits factor concentration and scaling metadata for `MPI` and `LCC`
- does not replay `AES-01` through `AES-03`

## Next Packet

`AES-05: Capacity & Crowding Risk Engine`
