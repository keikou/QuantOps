# Lane Surface Inventory

Date: `2026-04-06`
Repo: `QuantOps_github`
Status: `initial_lane_surface_inventory`

## Purpose

This file groups operator-visible `system` surfaces by lane so a reader can understand a checkpoint family without scanning endpoint lists one route at a time.

## Deployment / Rollout Intelligence

- `GET /system/deployment-rollout-decision/latest`
- `GET /system/deployment-rollout-candidate-docket/latest`
- `GET /system/deployment-rollout-state/latest`
- `GET /system/deployment-rollout-consumption/latest`
- `GET /system/deployment-rollout-effectiveness/latest`

Contract progression:

- decision
- approval docket
- persisted state
- applied consumption
- realized effectiveness

## Live Capital Control / Adaptive Runtime Allocation

- `GET /system/live-capital-control/latest`
- `GET /system/live-capital-adjustment-decision/latest`
- `GET /system/live-capital-control-state/latest`
- `GET /system/live-capital-control-consumption/latest`
- `GET /system/live-capital-control-effectiveness/latest`

Contract progression:

- live control posture
- adjustment decision
- persisted control state
- applied budget consumption
- realized control effectiveness

## Meta Portfolio Intelligence / Cross-Strategy Capital Allocation

- `GET /system/meta-portfolio-allocation/latest`
- `GET /system/meta-portfolio-decision/latest`
- `GET /system/meta-portfolio-state/latest`
- `GET /system/meta-portfolio-flow/latest`
- `GET /system/meta-portfolio-efficiency/latest`

Contract progression:

- allocation view
- capital decision
- persisted meta state
- share flow
- realized efficiency

## Learning / Policy Families

- `GET /system/learning-feedback/latest`
- `GET /system/learning-policy-updates/latest`
- `GET /system/learning-policy-state/latest`
- `GET /system/learning-resolved-overrides/latest`
- `GET /system/learning-applied-consumption/latest`
- `GET /system/policy-effectiveness/latest`
- `GET /system/policy-tuning/latest`
- `GET /system/meta-policy-state/latest`
- `GET /system/meta-policy-consumption/latest`
- `GET /system/meta-policy-effectiveness/latest`

Contract progression:

- learning signal
- policy update proposal
- persisted policy state
- applied override or tuning consumption
- realized policy effectiveness

## Strategy Evolution / Regime Adaptation Intelligence

- `GET /system/regime-state/latest`
- `GET /system/strategy-regime-compatibility/latest`
- `GET /system/strategy-gating-decision/latest`
- `GET /system/regime-transition-detection/latest`
- `GET /system/strategy-survival-analysis/latest`

## Autonomous Alpha Expansion / Strategy Generation Intelligence

- `GET /system/alpha-discovery-candidates/latest`
- `GET /system/alpha-validation-results/latest`
- `GET /system/alpha-admission-decision/latest`
- `GET /system/alpha-lifecycle-state/latest`
- `GET /system/alpha-inventory-health/latest`
- `GET /system/alpha-generation-agenda/latest`
- `GET /system/alpha-experiment-docket/latest`
- `GET /system/alpha-replacement-decision/latest`
- `GET /system/alpha-replacement-state/latest`
- `GET /system/alpha-expansion-effectiveness/latest`
- `GET /system/alpha-runtime-deployment-candidates/latest`
- `GET /system/alpha-runtime-governance-feedback/latest`
- `GET /system/alpha-runtime-rollback-response/latest`
- `GET /system/alpha-runtime-champion-challenger/latest`
- `GET /system/alpha-runtime-expansion-effectiveness/latest`
- `GET /system/alpha-next-cycle-learning-input/latest`
- `GET /system/alpha-next-cycle-policy-bridge/latest`
- `GET /system/alpha-regime-adaptation-input/latest`
- `GET /system/alpha-universe-refresh-priorities/latest`
- `GET /system/alpha-expansion-learning-effectiveness/latest`
- `GET /system/alpha-promotion-bridge/latest`
- `GET /system/alpha-family-capital-intent/latest`
- `GET /system/alpha-portfolio-intake-queue/latest`
- `GET /system/alpha-governed-universe-state/latest`
- `GET /system/alpha-strategy-factory-readiness/latest`

Contract progression:

- discovery queue
- validation truth
- admission decision
- lifecycle visibility
- inventory replacement health
- generation agenda
- experiment docket
- replacement decision
- replacement state
- expansion effectiveness
- runtime deployment candidates
- runtime governance feedback
- runtime rollback response
- runtime champion-challenger control
- runtime expansion effectiveness
- next-cycle learning input
- next-cycle policy bridge
- regime adaptation input
- universe refresh priorities
- alpha expansion learning effectiveness
- promotion bridge
- family capital intent
- portfolio intake queue
- governed universe state
- strategy factory readiness

## Rule

When a lane checkpoint becomes operationally visible through `/system/*`, add its family here as one grouped inventory rather than leaving the surface readable only from isolated endpoint rows.
