# Endpoint Contract Matrix

Date: `2026-04-05`
Repo: `QuantOps_github`
Status: `initial_endpoint_contract_matrix`

## Purpose

This file is the compact routing matrix for the current `system` contract surfaces.

## Core System Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/health` | base health contract | health payload |
| `GET /health` | legacy health contract | health payload |
| `GET /system/operator-diagnostic-bundle` | operator bundle | diagnostic bundle |
| `GET /system/recovery-replay-diagnostic-bundle` | recovery bundle | replay bundle |
| `GET /system/hardening-status` | hardening state | hardening summary |
| `GET /system/hardening-evidence-snapshot/latest` | hardening evidence | evidence snapshot |
| `GET /system/hardening-architect-handoff/latest` | architect bundle | handoff packet |
| `GET /system/resume-operator-packet/latest` | resume bundle | operator packet |

## Learning And Policy Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/learning-feedback/latest` | learning summary | feedback bundle |
| `GET /system/learning-policy-updates/latest` | policy updates | update list |
| `GET /system/learning-policy-state/latest` | persisted learning state | policy state |
| `GET /system/learning-resolved-overrides/latest` | resolved overrides | override bundle |
| `GET /system/learning-applied-consumption/latest` | applied consumption | consumed overrides |
| `GET /system/policy-effectiveness/latest` | policy effectiveness | effectiveness bundle |
| `GET /system/policy-tuning/latest` | policy tuning | recommendation bundle |
| `GET /system/meta-policy-state/latest` | meta-policy state | persisted state |
| `GET /system/meta-policy-consumption/latest` | meta-policy consumption | applied tuning |
| `GET /system/meta-policy-effectiveness/latest` | meta-policy outcome | effectiveness bundle |

## Deployment, Capital, And Meta-Portfolio Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/deployment-rollout-decision/latest` | rollout decision | stage decision |
| `GET /system/deployment-rollout-candidate-docket/latest` | rollout docket | approval docket |
| `GET /system/deployment-rollout-state/latest` | rollout state | persisted rollout state |
| `GET /system/deployment-rollout-consumption/latest` | rollout consumption | applied rollout posture |
| `GET /system/deployment-rollout-effectiveness/latest` | rollout effectiveness | outcome classification |
| `GET /system/live-capital-control/latest` | live capital governor | control posture |
| `GET /system/live-capital-adjustment-decision/latest` | capital decision | adjustment action |
| `GET /system/live-capital-control-state/latest` | capital state | persisted control state |
| `GET /system/live-capital-control-consumption/latest` | capital consumption | used budget view |
| `GET /system/live-capital-control-effectiveness/latest` | capital effectiveness | control effectiveness |
| `GET /system/meta-portfolio-allocation/latest` | meta allocation | allocation share view |
| `GET /system/meta-portfolio-decision/latest` | meta decision | decision action |
| `GET /system/meta-portfolio-state/latest` | meta state | persisted meta state |
| `GET /system/meta-portfolio-flow/latest` | meta flow | capital flow view |
| `GET /system/meta-portfolio-efficiency/latest` | meta efficiency | efficiency classification |

## Strategy Evolution / Regime Adaptation Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/regime-state/latest` | regime state | deterministic regime summary |
| `GET /system/strategy-regime-compatibility/latest` | regime compatibility | family compatibility view |
| `GET /system/strategy-gating-decision/latest` | gating decision | family gating action |
| `GET /system/regime-transition-detection/latest` | transition detection | family transition view |
| `GET /system/strategy-survival-analysis/latest` | survival analysis | family survival posture |

## Autonomous Alpha Expansion / Strategy Generation Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/alpha-discovery-candidates/latest` | alpha discovery | candidate expansion queue |
| `GET /system/alpha-validation-results/latest` | alpha validation | validation truth bundle |
| `GET /system/alpha-admission-decision/latest` | alpha admission | deterministic inventory admission |
| `GET /system/alpha-lifecycle-state/latest` | alpha lifecycle | lifecycle stage view |
| `GET /system/alpha-inventory-health/latest` | inventory health | replacement health posture |

## Rule

When a new `system` endpoint is added, update this matrix if the endpoint is operator-visible or part of the lane checkpoint contract surface.

Use `lane_surface_inventory.md` when you need to follow the same endpoints as one checkpoint family rather than as isolated routes.
