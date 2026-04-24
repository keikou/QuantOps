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
| `GET /system/alpha-generation-agenda/latest` | generation agenda | next alpha generation queue |
| `GET /system/alpha-experiment-docket/latest` | experiment docket | experiment execution docket |
| `GET /system/alpha-replacement-decision/latest` | replacement decision | deterministic replacement action |
| `GET /system/alpha-replacement-state/latest` | replacement state | replacement state view |
| `GET /system/alpha-expansion-effectiveness/latest` | expansion effectiveness | replacement effectiveness posture |
| `GET /system/alpha-runtime-deployment-candidates/latest` | runtime deployment | deployable runtime alpha candidates |
| `GET /system/alpha-runtime-governance-feedback/latest` | runtime feedback | live review and decay posture |
| `GET /system/alpha-runtime-rollback-response/latest` | runtime rollback | rollback and reduction response |
| `GET /system/alpha-runtime-champion-challenger/latest` | runtime competition | runtime winner control |
| `GET /system/alpha-runtime-expansion-effectiveness/latest` | runtime expansion effectiveness | runtime alpha expansion posture |
| `GET /system/alpha-next-cycle-learning-input/latest` | next-cycle learning input | alpha runtime feedback for next-cycle learning |
| `GET /system/alpha-next-cycle-policy-bridge/latest` | next-cycle policy bridge | alpha-family bridge into policy posture |
| `GET /system/alpha-regime-adaptation-input/latest` | regime adaptation input | alpha-family adaptation pressure |
| `GET /system/alpha-universe-refresh-priorities/latest` | universe refresh priorities | family expansion or prune queue |
| `GET /system/alpha-expansion-learning-effectiveness/latest` | expansion learning effectiveness | closed-loop alpha expansion posture |
| `GET /system/alpha-promotion-bridge/latest` | promotion bridge | alpha promotion acceleration pressure |
| `GET /system/alpha-family-capital-intent/latest` | family capital intent | family capacity expansion or constraint |
| `GET /system/alpha-portfolio-intake-queue/latest` | portfolio intake queue | alpha intake ordering and posture |
| `GET /system/alpha-governed-universe-state/latest` | governed universe state | governed alpha expansion or prune state |
| `GET /system/alpha-strategy-factory-readiness/latest` | strategy factory readiness | operational alpha factory readiness |

## Alpha Synthesis / Structural Discovery Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/alpha-synthesis-candidates/latest` | synthesis candidates | generated symbolic alpha candidates |
| `GET /system/alpha-structure-search-state/latest` | structure search state | active symbolic search state |
| `GET /system/alpha-novelty-evaluation/latest` | novelty evaluation | novelty scoring against expression library |
| `GET /system/alpha-expression-library/latest` | expression library | persisted symbolic expression inventory |
| `GET /system/alpha-synthesis-effectiveness/latest` | synthesis effectiveness | symbolic generator quality posture |
| `GET /system/alpha-parent-candidates/latest` | parent candidates | eligible parent expressions |
| `GET /system/alpha-mutation-candidates/latest` | mutation candidates | generated mutation expressions |
| `GET /system/alpha-crossover-candidates/latest` | crossover candidates | generated crossover expressions |
| `GET /system/alpha-evolution-search-state/latest` | evolution search state | evolutionary search router state |
| `GET /system/alpha-evolution-effectiveness/latest` | evolution effectiveness | evolutionary generator quality posture |
| `GET /system/alpha-regime-synthesis-agenda/latest` | regime synthesis agenda | regime-conditioned search agenda |
| `GET /system/alpha-regime-targeted-candidates/latest` | regime targeted candidates | candidates targeted to current regime |
| `GET /system/alpha-regime-fit-evaluation/latest` | regime fit evaluation | candidate-to-regime fit posture |
| `GET /system/alpha-regime-expression-map/latest` | regime expression map | family expression map by regime |
| `GET /system/alpha-regime-synthesis-effectiveness/latest` | regime synthesis effectiveness | regime-conditioned generator quality posture |
| `GET /system/alpha-hypothesis-agenda/latest` | hypothesis agenda | regime-conditioned hypothesis briefs |
| `GET /system/alpha-llm-hypothesis-prompts/latest` | llm hypothesis prompts | constrained prompt packs for symbolic translation |
| `GET /system/alpha-llm-translation-candidates/latest` | llm translation candidates | translated symbolic drafts from hypothesis briefs |
| `GET /system/alpha-hypothesis-critique/latest` | hypothesis critique | critique posture for translated drafts |
| `GET /system/alpha-hypothesis-effectiveness/latest` | hypothesis effectiveness | llm-assisted hypothesis generator quality posture |
| `GET /system/alpha-hypothesis-feedback-queue/latest` | hypothesis feedback queue | critique-derived feedback actions |
| `GET /system/alpha-hypothesis-prompt-tuning/latest` | hypothesis prompt tuning | deterministic prompt constraint recommendations |
| `GET /system/alpha-synthesis-policy-updates/latest` | synthesis policy updates | generator policy updates from feedback loop |
| `GET /system/alpha-feedback-learning-state/latest` | feedback learning state | feedback-loop learning posture |
| `GET /system/alpha-feedback-optimization-effectiveness/latest` | feedback optimization effectiveness | closed-loop synthesis feedback quality posture |

## Rule

When a new `system` endpoint is added, update this matrix if the endpoint is operator-visible or part of the lane checkpoint contract surface.

Use `lane_surface_inventory.md` when you need to follow the same endpoints as one checkpoint family rather than as isolated routes.
