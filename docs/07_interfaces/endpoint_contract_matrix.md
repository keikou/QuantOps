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

## Alpha Evaluation / Selection Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `GET /system/alpha-evaluation/latest` | alpha evaluation | evaluation summary across current candidates |
| `GET /system/alpha-decay-analysis/latest` | decay analysis | decay posture for evaluated alpha |
| `GET /system/alpha-correlation-matrix/latest` | correlation matrix | redundancy and correlation view |
| `GET /system/alpha-robustness-ranking/latest` | robustness ranking | stability-ranked alpha candidates |
| `GET /system/alpha-selection-decisions/latest` | selection decisions | promote/watch/reject decisions |
| `POST /system/alpha-evaluation/run` | evaluation run trigger | explicit evaluation execution request |
| `GET /system/alpha-evaluation/candidate/{alpha_id}` | candidate evaluation lookup | per-alpha evaluation detail |
| `POST /system/alpha-walk-forward/run` | walk-forward run trigger | explicit walk-forward validation execution request |
| `GET /system/alpha-walk-forward/latest` | walk-forward latest | latest validation summary across candidates |
| `GET /system/alpha-walk-forward/candidate/{alpha_id}` | walk-forward candidate lookup | per-alpha walk-forward detail |
| `GET /system/alpha-oos-validation/latest` | oos validation | out-of-sample validation summary |
| `GET /system/alpha-validation-decisions/latest` | validation decisions | pass/watch/fail validation decisions |
| `GET /system/alpha-validation-failures/latest` | validation failures | explicit failed validation reasons |
| `POST /system/alpha-factor-attribution/run` | factor attribution run trigger | explicit attribution execution request |
| `GET /system/alpha-factor-attribution/latest` | factor attribution latest | latest attribution summary across selected alpha |
| `GET /system/alpha-factor-attribution/candidate/{alpha_id}` | attribution candidate lookup | per-alpha attribution detail |
| `GET /system/alpha-factor-exposure/latest` | factor exposure | per-factor loading view |
| `GET /system/alpha-residual-alpha/latest` | residual alpha | factor-explained versus residual alpha view |
| `GET /system/alpha-economic-risk/latest` | economic risk | regime and factor fragility view |
| `GET /system/alpha-factor-concentration/latest` | factor concentration | ensemble factor concentration view |
| `GET /system/alpha-economic-meaning/latest` | economic meaning | economic label and scaling recommendation |
| `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}` | ensemble attribution lookup | per-ensemble attribution detail |
| `POST /system/alpha-capacity/run` | capacity run trigger | explicit capacity and crowding execution request |
| `GET /system/alpha-capacity/latest` | capacity latest | latest per-alpha capacity summary |
| `GET /system/alpha-capacity/candidate/{alpha_id}` | capacity candidate lookup | per-alpha capacity, impact, and crowding detail |
| `GET /system/alpha-crowding/latest` | crowding risk | crowding and overlap risk view |
| `GET /system/alpha-impact/latest` | impact model | market impact and impact-adjusted return view |
| `GET /system/alpha-capacity/ensemble/{ensemble_id}` | ensemble capacity lookup | per-ensemble capacity limit and scaling decision |
| `POST /system/alpha-dynamic-weights/run` | dynamic weighting run trigger | explicit dynamic alpha weighting execution request |
| `GET /system/alpha-dynamic-weights/latest` | dynamic weights latest | latest target, smoothed, and constrained alpha weights |
| `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}` | ensemble dynamic weights lookup | per-ensemble dynamic weight proposal detail |
| `GET /system/alpha-weight-adjustments/latest` | weight adjustments | latest alpha weight adjustment reasons |
| `GET /system/alpha-weight-drift/latest` | weight drift | weight delta and drift flag view |
| `GET /system/alpha-weight-constraints/latest` | weight constraints | turnover, max-weight, and capacity constraint events |
| `GET /system/alpha-weight-proposals/latest` | weight proposals | MPI-ready proposal and LCC review metadata |
| `POST /system/alpha-kill-switch/run` | kill-switch run trigger | explicit alpha kill-switch and retirement execution request |
| `GET /system/alpha-kill-switch/latest` | kill-switch latest | latest alpha stop, freeze, reduce, and continue decisions |
| `GET /system/alpha-kill-switch/alpha/{alpha_id}` | alpha kill-switch lookup | per-alpha health, decision, and event detail |
| `GET /system/alpha-retirement/latest` | retirement latest | latest retirement decision summary |
| `GET /system/alpha-retirement/alpha/{alpha_id}` | alpha retirement lookup | per-alpha retirement and lifecycle update detail |
| `GET /system/alpha-deactivation-decisions/latest` | deactivation decisions | alpha reduce, freeze, and retire action list |
| `GET /system/alpha-kill-switch-events/latest` | kill-switch events | stop, freeze, and reduce event log |
| `POST /system/alpha-kill-switch/override` | kill-switch override | operator override record |
| `POST /system/alpha-feedback-loop/run` | feedback loop run trigger | explicit self-improving alpha loop execution request |
| `GET /system/alpha-feedback-loop/latest` | feedback loop latest | latest realized alpha outcomes and learning signals |
| `GET /system/alpha-learning-signals/latest` | learning signals | alpha outcome classes and learning actions |
| `GET /system/alpha-generation-priors/latest` | generation priors | bounded ASD generation prior recommendations |
| `GET /system/alpha-family-performance/latest` | family performance | alpha family realized performance and recommendation |
| `GET /system/alpha-policy-recommendations/latest` | policy recommendations | bounded AES/ASD/AAE policy recommendations |
| `GET /system/alpha-feedback-loop/alpha/{alpha_id}` | alpha feedback lookup | per-alpha outcome and motif context |
| `GET /system/alpha-feedback-loop/family/{family_id}` | family feedback lookup | per-family performance and prior context |
| `POST /system/alpha-policy-recommendations/apply` | policy application record | operator-controlled policy application record |

## Operational Risk & Control Surfaces

| Endpoint | Contract role | Primary output |
| --- | --- | --- |
| `POST /system/operational-risk/run` | operational risk run trigger | explicit system-level risk evaluation execution request |
| `GET /system/risk-state/latest` | risk state latest | global and domain risk levels |
| `GET /system/global-risk-metrics/latest` | global risk metrics | data, execution, portfolio, alpha-system, and infra risk metrics |
| `GET /system/anomaly-detection/latest` | anomaly detection | operational anomaly records by domain |
| `GET /system/operational-incidents/latest` | operational incidents | grouped system-level incidents |
| `GET /system/risk-response/latest` | risk response | recommended reduce, freeze, halt, or monitor actions |
| `POST /system/risk-response/execute` | response execution record | operator-approved response execution record |
| `POST /system/global-kill-switch` | global kill switch event | global or scoped kill-switch event record |
| `GET /system/global-kill-switch/latest` | global kill switch latest | latest kill-switch event log |
| `POST /system/operational-risk/override` | operational risk override | operator override audit record |
| `POST /system/risk-response/orchestrate` | risk response orchestration trigger | explicit safe-mode and response orchestration request |
| `GET /system/risk-response-orchestration/latest` | response orchestration latest | latest LCC and execution response payloads |
| `GET /system/runtime-safe-mode/latest` | runtime safe mode latest | current allowed and blocked order modes by risk state |
| `GET /system/order-permission-matrix/latest` | order permission matrix | risk-level order permission matrix |
| `GET /system/risk-recovery-readiness/latest` | recovery readiness | required checks and readiness state for risk recovery |
| `POST /system/risk-recovery/request` | risk recovery request | operator recovery request record |
| `POST /system/execution-health/run` | execution health run trigger | explicit execution and broker health evaluation request |
| `GET /system/execution-health/latest` | execution health latest | latest broker, venue, and execution health summary |
| `GET /system/broker-health/latest` | broker health latest | broker heartbeat, reject, cancel, replace, and sync health |
| `GET /system/venue-health/latest` | venue health latest | venue fill, slippage, latency, reject, and partial fill health |
| `GET /system/execution-anomalies/latest` | execution anomalies | execution-domain anomaly records |
| `GET /system/execution-incidents/latest` | execution incidents | grouped execution incidents and recommended actions |
| `GET /system/execution-safe-mode-recommendation/latest` | execution safe-mode recommendation | ORC-compatible execution safe-mode recommendation |
| `GET /system/broker-health/{broker_id}` | broker health lookup | per-broker health detail |
| `GET /system/venue-health/{venue_id}` | venue health lookup | per-venue health detail |
| `POST /system/data-integrity/run` | data integrity run trigger | explicit data integrity and feed reliability evaluation request |
| `GET /system/data-integrity/latest` | data integrity latest | latest feed and symbol data health summary |
| `GET /system/market-feed-health/latest` | market feed health latest | feed freshness, missing, bad tick, latency, and coverage health |
| `GET /system/market-feed-health/{feed_id}` | market feed health lookup | per-feed health detail |
| `GET /system/symbol-data-health/latest` | symbol data health latest | per-symbol data health and mark reliability view |
| `GET /system/symbol-data-health/{symbol}` | symbol data health lookup | per-symbol data integrity detail |
| `GET /system/data-anomalies/latest` | data anomalies | data-domain anomaly records |
| `GET /system/data-incidents/latest` | data incidents | grouped data incidents and recommended actions |
| `GET /system/mark-reliability/latest` | mark reliability | mark price reliability state |
| `GET /system/data-safe-mode-recommendation/latest` | data safe-mode recommendation | ORC-compatible data safe-mode recommendation |
| `POST /system/orc-governance/sync` | ORC governance sync trigger | explicit incident audit and governance staging request |
| `GET /system/orc-governance/latest` | ORC governance latest | latest governance incident and approval summary |
| `GET /system/orc-governance/incidents/latest` | governance incidents | ORC incidents converted into governance-visible records |
| `GET /system/orc-governance/incident/{incident_id}` | governance incident lookup | per-incident governance state and approval link |
| `GET /system/orc-governance/pending-approvals/latest` | pending approvals | AFG-compatible approval staging links |
| `GET /system/orc-governance/audit/latest` | governance audit | ORC governance audit event log |
| `POST /system/orc-governance/recovery/request` | governance recovery request | operator recovery governance request |
| `GET /system/orc-governance/recovery/latest` | governance recovery latest | latest recovery governance decisions |

## Rule

When a new `system` endpoint is added, update this matrix if the endpoint is operator-visible or part of the lane checkpoint contract surface.

Use `lane_surface_inventory.md` when you need to follow the same endpoints as one checkpoint family rather than as isolated routes.
