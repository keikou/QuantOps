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

## Alpha Synthesis / Structural Discovery Intelligence

- `GET /system/alpha-synthesis-candidates/latest`
- `GET /system/alpha-structure-search-state/latest`
- `GET /system/alpha-novelty-evaluation/latest`
- `GET /system/alpha-expression-library/latest`
- `GET /system/alpha-synthesis-effectiveness/latest`
- `GET /system/alpha-parent-candidates/latest`
- `GET /system/alpha-mutation-candidates/latest`
- `GET /system/alpha-crossover-candidates/latest`
- `GET /system/alpha-evolution-search-state/latest`
- `GET /system/alpha-evolution-effectiveness/latest`
- `GET /system/alpha-regime-synthesis-agenda/latest`
- `GET /system/alpha-regime-targeted-candidates/latest`
- `GET /system/alpha-regime-fit-evaluation/latest`
- `GET /system/alpha-regime-expression-map/latest`
- `GET /system/alpha-regime-synthesis-effectiveness/latest`
- `GET /system/alpha-hypothesis-agenda/latest`
- `GET /system/alpha-llm-hypothesis-prompts/latest`
- `GET /system/alpha-llm-translation-candidates/latest`
- `GET /system/alpha-hypothesis-critique/latest`
- `GET /system/alpha-hypothesis-effectiveness/latest`
- `GET /system/alpha-hypothesis-feedback-queue/latest`
- `GET /system/alpha-hypothesis-prompt-tuning/latest`
- `GET /system/alpha-synthesis-policy-updates/latest`
- `GET /system/alpha-feedback-learning-state/latest`
- `GET /system/alpha-feedback-optimization-effectiveness/latest`

Contract progression:

- generated symbolic structures
- structure search state
- novelty scoring
- expression library visibility
- synthesis effectiveness
- parent selection
- mutation search
- crossover search
- evolution router state
- evolution effectiveness
- regime synthesis agenda
- regime-targeted candidates
- regime-fit evaluation
- regime expression map
- regime synthesis effectiveness
- hypothesis agenda
- llm hypothesis prompts
- llm translation candidates
- hypothesis critique
- hypothesis effectiveness
- hypothesis feedback queue
- hypothesis prompt tuning
- synthesis policy updates
- feedback learning state
- feedback optimization effectiveness

## Alpha Evaluation / Selection Intelligence

- `GET /system/alpha-evaluation/latest`
- `GET /system/alpha-decay-analysis/latest`
- `GET /system/alpha-correlation-matrix/latest`
- `GET /system/alpha-robustness-ranking/latest`
- `GET /system/alpha-selection-decisions/latest`
- `POST /system/alpha-evaluation/run`
- `GET /system/alpha-evaluation/candidate/{alpha_id}`
- `POST /system/alpha-walk-forward/run`
- `GET /system/alpha-walk-forward/latest`
- `GET /system/alpha-walk-forward/candidate/{alpha_id}`
- `GET /system/alpha-oos-validation/latest`
- `GET /system/alpha-validation-decisions/latest`
- `GET /system/alpha-validation-failures/latest`
- `POST /system/alpha-factor-attribution/run`
- `GET /system/alpha-factor-attribution/latest`
- `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
- `GET /system/alpha-factor-exposure/latest`
- `GET /system/alpha-residual-alpha/latest`
- `GET /system/alpha-economic-risk/latest`
- `GET /system/alpha-factor-concentration/latest`
- `GET /system/alpha-economic-meaning/latest`
- `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`
- `POST /system/alpha-capacity/run`
- `GET /system/alpha-capacity/latest`
- `GET /system/alpha-capacity/candidate/{alpha_id}`
- `GET /system/alpha-crowding/latest`
- `GET /system/alpha-impact/latest`
- `GET /system/alpha-capacity/ensemble/{ensemble_id}`
- `POST /system/alpha-dynamic-weights/run`
- `GET /system/alpha-dynamic-weights/latest`
- `GET /system/alpha-dynamic-weights/ensemble/{ensemble_id}`
- `GET /system/alpha-weight-adjustments/latest`
- `GET /system/alpha-weight-drift/latest`
- `GET /system/alpha-weight-constraints/latest`
- `GET /system/alpha-weight-proposals/latest`
- `POST /system/alpha-kill-switch/run`
- `GET /system/alpha-kill-switch/latest`
- `GET /system/alpha-kill-switch/alpha/{alpha_id}`
- `GET /system/alpha-retirement/latest`
- `GET /system/alpha-retirement/alpha/{alpha_id}`
- `GET /system/alpha-deactivation-decisions/latest`
- `GET /system/alpha-kill-switch-events/latest`
- `POST /system/alpha-kill-switch/override`
- `POST /system/alpha-feedback-loop/run`
- `GET /system/alpha-feedback-loop/latest`
- `GET /system/alpha-learning-signals/latest`
- `GET /system/alpha-generation-priors/latest`
- `GET /system/alpha-family-performance/latest`
- `GET /system/alpha-policy-recommendations/latest`
- `GET /system/alpha-feedback-loop/alpha/{alpha_id}`
- `GET /system/alpha-feedback-loop/family/{family_id}`
- `POST /system/alpha-policy-recommendations/apply`

Contract progression:

- evaluation summary
- decay analysis
- correlation and redundancy view
- robustness ranking
- selection decisions
- explicit run trigger
- per-candidate evaluation lookup
- explicit walk-forward run trigger
- latest walk-forward validation summary
- per-candidate walk-forward detail
- oos validation summary
- validation decisions
- validation failures
- explicit factor attribution run trigger
- latest factor attribution summary
- per-alpha attribution detail
- factor exposure view
- residual alpha view
- economic risk view
- factor concentration view
- economic meaning labels and scaling recommendation
- per-ensemble attribution detail
- explicit capacity run trigger
- per-alpha capacity summary
- per-alpha capacity detail
- crowding risk view
- market impact view
- per-ensemble capacity limit and scaling decision
- explicit dynamic weighting run trigger
- latest dynamic weights summary
- per-ensemble dynamic weights detail
- weight adjustment reason view
- weight drift view
- weight constraint event view
- MPI-ready proposal and LCC review metadata
- explicit alpha kill-switch run trigger
- latest kill-switch decision summary
- per-alpha kill-switch detail
- retirement decision summary
- per-alpha lifecycle update detail
- deactivation decision list
- kill-switch event log
- operator override record
- explicit feedback loop run trigger
- realized alpha outcome and learning signal summary
- learning signal view
- generation prior recommendation view
- family performance recommendation view
- bounded policy recommendation view
- per-alpha feedback detail
- per-family feedback detail
- operator-controlled policy application record

## Operational Risk & Control Intelligence

- `POST /system/operational-risk/run`
- `GET /system/risk-state/latest`
- `GET /system/global-risk-metrics/latest`
- `GET /system/anomaly-detection/latest`
- `GET /system/operational-incidents/latest`
- `GET /system/risk-response/latest`
- `POST /system/risk-response/execute`
- `POST /system/global-kill-switch`
- `GET /system/global-kill-switch/latest`
- `POST /system/operational-risk/override`
- `POST /system/risk-response/orchestrate`
- `GET /system/risk-response-orchestration/latest`
- `GET /system/runtime-safe-mode/latest`
- `GET /system/order-permission-matrix/latest`
- `GET /system/risk-recovery-readiness/latest`
- `POST /system/risk-recovery/request`
- `POST /system/execution-health/run`
- `GET /system/execution-health/latest`
- `GET /system/broker-health/latest`
- `GET /system/venue-health/latest`
- `GET /system/execution-anomalies/latest`
- `GET /system/execution-incidents/latest`
- `GET /system/execution-safe-mode-recommendation/latest`
- `GET /system/broker-health/{broker_id}`
- `GET /system/venue-health/{venue_id}`
- `POST /system/data-integrity/run`
- `GET /system/data-integrity/latest`
- `GET /system/market-feed-health/latest`
- `GET /system/market-feed-health/{feed_id}`
- `GET /system/symbol-data-health/latest`
- `GET /system/symbol-data-health/{symbol}`
- `GET /system/data-anomalies/latest`
- `GET /system/data-incidents/latest`
- `GET /system/mark-reliability/latest`
- `GET /system/data-safe-mode-recommendation/latest`
- `POST /system/orc-governance/sync`
- `GET /system/orc-governance/latest`
- `GET /system/orc-governance/incidents/latest`
- `GET /system/orc-governance/incident/{incident_id}`
- `GET /system/orc-governance/pending-approvals/latest`
- `GET /system/orc-governance/audit/latest`
- `POST /system/orc-governance/recovery/request`
- `GET /system/orc-governance/recovery/latest`

Contract progression:

- explicit operational risk run trigger
- global and domain risk state
- system-level risk metric view
- anomaly detection view
- operational incident grouping
- response recommendation view
- response execution record
- global kill-switch event record
- kill-switch event log
- operator override audit record
- explicit risk response orchestration trigger
- LCC and execution response payload view
- runtime safe-mode contract view
- order permission matrix view
- recovery readiness view
- operator recovery request record
- explicit execution health run trigger
- broker and venue health summary
- broker health state view
- venue health state view
- execution anomaly view
- execution incident view
- execution safe-mode recommendation
- per-broker health detail
- per-venue health detail
- explicit data integrity run trigger
- feed and symbol data health summary
- market feed health state
- per-feed health detail
- symbol data health state
- per-symbol health detail
- data anomaly view
- data incident view
- mark reliability view
- data safe-mode recommendation
- explicit ORC governance sync trigger
- incident governance record view
- per-incident governance lookup
- AFG-compatible pending approval staging
- governance audit event log
- recovery governance request
- recovery governance state

## Alpha Factory Governance / Operator Control

- `POST /system/operator-action/submit`
- `GET /system/operator-actions/latest`
- `GET /system/pending-approvals/latest`
- `GET /system/pending-approvals/{approval_id}`
- `POST /system/pending-approvals/{approval_id}/approve`
- `POST /system/pending-approvals/{approval_id}/reject`
- `POST /system/operator-override`
- `GET /system/operator-overrides/latest`
- `POST /system/operator-overrides/{override_id}/expire`
- `GET /system/audit-log/latest`
- `GET /system/governance-state/latest`
- `POST /system/governance/sync`
- `POST /system/governance/dispatch`
- `GET /system/governance/dispatch/latest`

Contract progression:

- operator action submission
- policy-gated action decision
- pending approval queue
- approval / rejection decision
- time-limited operator override
- governance audit log
- governance mode and queue counters
- ORC-to-AFG sync
- dispatch staging and dry-run
- generic runtime enforcement check
- pre-dispatch enforcement
- pre-allocation enforcement
- pre-execution enforcement
- pre-lifecycle enforcement
- pre-policy-apply enforcement
- enforcement check log
- enforcement violation log
- runtime constraint log
- enforcement consistency state
- authorization check
- authorization decision log
- authorization denial log
- role registry
- permission registry
- actor-role assignment
- actor-role revoke
- actor permission expansion
- authorization audit log

AFG-02 additions:

- `POST /system/policy-enforcement/check`
- `POST /system/policy-enforcement/pre-dispatch`
- `POST /system/policy-enforcement/pre-allocation`
- `POST /system/policy-enforcement/pre-execution`
- `POST /system/policy-enforcement/pre-lifecycle`
- `POST /system/policy-enforcement/pre-policy-apply`
- `GET /system/policy-enforcement/latest`
- `GET /system/policy-enforcement/violations/latest`
- `GET /system/policy-enforcement/constraints/latest`
- `GET /system/policy-enforcement/state/latest`

AFG-03 additions:

- `POST /system/authorization/check`
- `GET /system/authorization/latest`
- `GET /system/authorization/denials/latest`
- `GET /system/roles/latest`
- `GET /system/permissions/latest`
- `POST /system/roles/assign`
- `POST /system/roles/revoke`
- `GET /system/actor-permissions/{actor_id}`
- `GET /system/authorization/audit/latest`

AFG-04 additions:

- `POST /system/incidents/ingest`
- `GET /system/incidents/latest`
- `POST /system/incidents/{id}/review`
- `POST /system/incidents/{id}/rca`
- `POST /system/incidents/{id}/actions`
- `POST /system/incidents/{id}/close`
- `GET /system/postmortem/latest`
- `POST /system/postmortem-feedback/build/{incident_id}`
- `POST /system/postmortem-feedback/dispatch/{feedback_id}`
- `GET /system/postmortem-feedback/latest`
- `GET /system/postmortem-feedback/target/{target_system}`
- `GET /system/postmortem-feedback/dispatch/latest`

AFG-04 progression:

- incident ingestion
- severity classification
- review lifecycle
- approved RCA
- action item tracking
- typed feedback generation
- approval-gated feedback dispatch
- dispatch audit and idempotency

AFG-05 additions:

- `GET /system/audit/bundle/{incident_id}`
- `POST /system/audit/replay/{incident_id}`
- `GET /system/audit/replay/{replay_id}`
- `GET /system/audit/export/{incident_id}`
- `GET /system/audit/bundles/latest`
- `GET /system/audit/replays/latest`
- `GET /system/audit/exports/latest`

AFG-05 progression:

- audit evidence bundle
- content hash and chain hash
- governance replay log
- decision trace
- approval trace
- feedback trace
- dispatch trace
- immutable JSON export
- AFG lane freeze readiness

## Rule

When a lane checkpoint becomes operationally visible through `/system/*`, add its family here as one grouped inventory rather than leaving the surface readable only from isolated endpoint rows.

## System Reliability / Runtime Hardening

SRH-01 additions:

- `POST /system/runtime-health/ingest`
- `GET /system/runtime-health/latest`
- `GET /system/runtime-health/components`
- `GET /system/runtime-health/signals/latest`
- `GET /system/degradation/latest`
- `GET /system/runtime-control/actions/latest`
- `POST /system/control/safe-mode`
- `GET /system/runtime-recovery/latest`

SRH-01 progression:

- health signal ingestion
- component health score
- composite system health score
- degradation detection
- throttle / safe mode / halt control action
- recovery attempt
- AFG freeze boundary preservation
