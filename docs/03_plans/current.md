# Current Plan

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Status: `live_capital_control_architect_judgment_pending`

## Current Planning Decision

The current hardening/resume slice is treated as sufficiently complete.

So the active planning question is:

- how should live capital keep changing after deployment once live truth materially changes?
- how should runtime health, risk usage, and execution quality constrain live allocation?
- how should stale static live allocation be prevented?

## Current Answer

Architect-selected answer:

- `Deployment / Rollout Intelligence v1` is checkpoint-complete through `DRI-05`
- next top-level lane is `Live Capital Control / Adaptive Runtime Allocation`
- first packet should be `LCC-01: Live Allocation Governor`

## Why This Is The Current Plan

Architect re-alignment now treats the following as sufficiently closed for the current slice:

- replay confidence
- cross-phase acceptance
- provenance and audit visibility
- runtime/governance linkage visibility
- operator and recovery diagnostic readiness
- resume/handover entrypoint coverage
- `Execution Reality v1`
- `Governance -> Runtime Control v1`
- `Portfolio Intelligence v1`
- `Alpha / Strategy Selection Intelligence v1`
- `Research / Promotion Intelligence v1`
- `System-Level Learning / Feedback Integration v1`
- `Policy Optimization / Meta-Control Learning v1`

That means planning should not continue to expand completed rollout packaging and should now start the first live-capital control lane.

## Explicitly Completed Planning Slice

The following planning sequence is now historical and completed:

1. define post-Phase7 hardening as a track, not `Phase8`
2. implement `Recovery / Replay Confidence`
3. implement `Cross-Phase Acceptance`
4. implement provenance and linkage packets
5. implement operator and recovery bundles
6. implement status, evidence, handoff, and resume surfaces
7. confirm with architect that the slice is sufficiently complete
8. complete the first five post-hardening intelligence lanes
9. complete `System-Level Learning / Feedback Integration v1` through `SLLFI-05`
10. freeze `SLLFI v1` as the first applied-consumption checkpoint
11. complete `Policy Optimization / Meta-Control Learning v1` through `PO-05`

## Current Lane Output

Current historical lane outputs:

- `../Policy_optimization_meta_control_learning_packet01_plan.md`
- `../../test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet01.py`
- `../Policy_optimization_meta_control_learning_packet02_tuning_recommendations_plan.md`
- `../../test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet02_tuning_recommendations.py`
- `../Policy_optimization_meta_control_learning_packet03_persisted_meta_policy_state_plan.md`
- `../../test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet03_persisted_meta_policy_state.py`
- `../Policy_optimization_meta_control_learning_packet04_applied_tuning_consumption_plan.md`
- `../../test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet04_applied_tuning_consumption.py`
- `../Policy_optimization_meta_control_learning_packet05_outcome_effectiveness_plan.md`
- `../../test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet05_outcome_effectiveness.py`

Current completed rollout outputs:

- `../Deployment_rollout_intelligence_packet01_plan.md`
- `../../test_bundle/scripts/verify_deployment_rollout_intelligence_packet01.py`
- `GET /system/deployment-rollout-decision/latest`
- `../Deployment_rollout_intelligence_packet02_candidate_docket_plan.md`
- `../../test_bundle/scripts/verify_deployment_rollout_intelligence_packet02_candidate_docket.py`
- `GET /system/deployment-rollout-candidate-docket/latest`
- `../Deployment_rollout_intelligence_packet03_persisted_rollout_state_plan.md`
- `../../test_bundle/scripts/verify_deployment_rollout_intelligence_packet03_persisted_rollout_state.py`
- `GET /system/deployment-rollout-state/latest`
- `../Deployment_rollout_intelligence_packet04_applied_rollout_consumption_plan.md`
- `../../test_bundle/scripts/verify_deployment_rollout_intelligence_packet04_applied_rollout_consumption.py`
- `GET /system/deployment-rollout-consumption/latest`
- `../Deployment_rollout_intelligence_packet05_rollout_outcome_effectiveness_plan.md`
- `../../test_bundle/scripts/verify_deployment_rollout_intelligence_packet05_rollout_outcome_effectiveness.py`
- `GET /system/deployment-rollout-effectiveness/latest`

Current completed live-capital outputs:

- `../Live_capital_control_adaptive_runtime_allocation_packet01_plan.md`
- `../../test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet01.py`
- `GET /system/live-capital-control/latest`
- `../Live_capital_control_adaptive_runtime_allocation_packet02_adjustment_decision_plan.md`
- `../../test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet02_adjustment_decision.py`
- `GET /system/live-capital-adjustment-decision/latest`
- `../Live_capital_control_adaptive_runtime_allocation_packet03_control_state_plan.md`
- `../../test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet03_control_state.py`
- `GET /system/live-capital-control-state/latest`
- `../Live_capital_control_adaptive_runtime_allocation_packet04_control_consumption_plan.md`
- `../../test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet04_control_consumption.py`
- `GET /system/live-capital-control-consumption/latest`
- `../Live_capital_control_adaptive_runtime_allocation_packet05_control_effectiveness_plan.md`
- `../../test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet05_control_effectiveness.py`
- `GET /system/live-capital-control-effectiveness/latest`

Current plan outputs now ready:

- `../Live_capital_control_adaptive_runtime_allocation_lane_status_review_2026-04-05.md`
- `../Live_capital_control_adaptive_runtime_allocation_architect_status_update_2026-04-05.md`
- `../Live_capital_control_adaptive_runtime_allocation_checkpoint_v1.md`
- `../Live_capital_control_adaptive_runtime_allocation_upward_report_2026-04-05.md`

Current plan output to decide next:

- architect judgment on whether to continue `LCC` or switch to the next top-level lane

## Non-Plan

This is not the current plan:

- another hardening-only lane
- another resume packaging lane
- another acceptance restart
- another `Execution Reality` expansion
- another `Governance -> Runtime Control` deepening step
- another `Portfolio Intelligence` deepening step
- another `Alpha / Strategy Selection Intelligence` deepening step
- another `Research / Promotion Intelligence` deepening step
- another `System-Level Learning / Feedback Integration` packet
- another `Policy Optimization` packet before rollout lane establishment
- replaying `DRI-01` instead of extending the rollout lane
- inventing `DRI-06` before freezing and reviewing the first checkpoint
- continuing `DRI` packet expansion before starting `LCC-01`

## Read Before Editing

1. `../04_tasks/current.md`
2. `../PO_checkpoint_resume_memo_2026-04-04.md`
3. `../Policy_optimization_meta_control_learning_architect_status_update_2026-04-03.md`
4. `../Cross_thread_resume_handover_2026-04-02.md`
5. `./roadmap.md`
