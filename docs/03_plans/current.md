# Current Plan

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Status: `strategy_evolution_regime_adaptation_intelligence_packet01_pending`

## Current Planning Decision

The current hardening/resume slice is treated as sufficiently complete.

So the active planning question is:

- how should live regime state become explicit enough to gate strategies deterministically?
- how should regime-consistent degradation be separated from stochastic noise?
- how should capital stop flowing to strategies whose live behavior no longer matches the current regime?

Historical note:

- `Execution Reality` was the earliest next-lane candidate after hardening/resume, but it is no longer the current active planning answer

## Current Answer

Architect-selected answer:

- `Live Capital Control / Adaptive Runtime Allocation v1` is checkpoint-complete through `LCC-05`
- `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1` is checkpoint-complete through `MPI-05`
- next top-level lane is `Strategy Evolution / Regime Adaptation Intelligence`
- first packets are now:
  - `SERI-01: Regime Detection & Strategy Gating Engine`
  - `SERI-02: Strategy Regime Compatibility Surface`
  - `SERI-03: Strategy Gating Decision`
  - `SERI-04: Regime Transition Detection`
  - `SERI-05: Strategy Survival Analysis`

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

That means planning should not continue to expand completed live-capital or meta-portfolio packaging and should now start the first regime-adaptation lane.

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
12. complete `Deployment / Rollout Intelligence v1` through `DRI-05`
13. complete `Live Capital Control / Adaptive Runtime Allocation v1` through `LCC-05`
14. complete `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1` through `MPI-05`

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

Current completed meta-portfolio outputs:

- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet01_plan.md`
- `../../test_bundle/scripts/verify_meta_portfolio_intelligence_cross_strategy_capital_allocation_packet01.py`
- `GET /system/meta-portfolio-allocation/latest`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet02_decision_plan.md`
- `../../test_bundle/scripts/verify_meta_portfolio_intelligence_cross_strategy_capital_allocation_packet02_decision.py`
- `GET /system/meta-portfolio-decision/latest`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet03_state_plan.md`
- `../../test_bundle/scripts/verify_meta_portfolio_intelligence_cross_strategy_capital_allocation_packet03_state.py`
- `GET /system/meta-portfolio-state/latest`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet04_flow_plan.md`
- `../../test_bundle/scripts/verify_meta_portfolio_intelligence_cross_strategy_capital_allocation_packet04_flow.py`
- `GET /system/meta-portfolio-flow/latest`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet05_efficiency_plan.md`
- `../../test_bundle/scripts/verify_meta_portfolio_intelligence_cross_strategy_capital_allocation_packet05_efficiency.py`
- `GET /system/meta-portfolio-efficiency/latest`

Current plan outputs now ready:

- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_lane_status_review_2026-04-05.md`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_architect_status_update_2026-04-05.md`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_checkpoint_v1.md`
- `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_upward_report_2026-04-05.md`

Current plan output to implement next:

- first `SERI` packet plan doc
- first `SERI` verifier script
- `GET /system/regime-state/latest`

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
- continuing `MPI` packet expansion after architect checkpoint closure
- inventing `MPI-06` before a real regression exists
- replaying a completed checkpoint lane instead of starting `SERI`

## Read Before Editing

1. `../04_tasks/current.md`
2. `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_architect_status_update_2026-04-05.md`
3. `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_checkpoint_v1.md`
4. `../Cross_thread_resume_handover_2026-04-02.md`
5. `./roadmap.md`
