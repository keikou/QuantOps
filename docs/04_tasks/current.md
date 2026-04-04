# Current Tasks

Date: `2026-04-05`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `strategy_evolution_regime_adaptation_intelligence`
Status: `packet01_pending`

## Purpose

This file is the canonical current-task entrypoint for both humans and AI agents.

It answers:

- what is active now
- what is explicitly not active now
- what should happen next if work resumes

## Current State

The current hardening slice is already treated as sufficiently complete.

That means:

- do not restart `Cross-Phase Acceptance`
- do not reopen `Recovery / Replay Confidence`
- do not deepen resume/handover packaging unless a real regression is found

## Active Task

Current top task:

- establish `Strategy Evolution / Regime Adaptation Intelligence` from the completed `MPI v1` checkpoint
- implement `SERI-01: Regime Detection & Strategy Gating Engine`

Current architect-selected candidate:

- `Strategy Evolution / Regime Adaptation Intelligence`
- current implementation boundary = `SERI-01`
- current dependency 1 = `Research / Promotion Intelligence v1 checkpoint through RPI-06`
- current dependency 2 = `Alpha / Strategy Selection Intelligence v1 checkpoint through ASI-05`
- current dependency 3 = `Portfolio Intelligence v1 checkpoint through PI-05`
- current dependency 4 = `Governance -> Runtime Control v1 checkpoint through C6`
- current dependency 5 = `Execution Reality v1 checkpoint through Packet 10`
- current dependency 6 = `System-Level Learning / Feedback Integration v1 checkpoint through SLLFI-05`
- current dependency 7 = `Policy Optimization / Meta-Control Learning v1 checkpoint through PO-05`
- current dependency 8 = `Deployment / Rollout Intelligence v1 checkpoint through DRI-05`
- current dependency 9 = `Live Capital Control / Adaptive Runtime Allocation v1 checkpoint through LCC-05`
- current dependency 10 = `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1 checkpoint through MPI-05`

## Why This Is The Active Task

Architect now treats `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1` as completed enough to start regime-adaptation control.

The next question is:

- "how should current regime state become explicit at the system surface?"
- "how should strategy gating react when degradation is regime-consistent?"
- "what is the first deterministic survival boundary for live strategies?"

This is still the next lane beyond the completed hardening/resume slice, but it is no longer the older `Execution Reality` default.

## Next Candidate Options

1. `Strategy Evolution / Regime Adaptation Intelligence`
   - selected by architect as the next top-level lane
2. `Deployment / Rollout Intelligence`
   - now treated as checkpoint-complete input, not the active lane
3. `Policy Optimization / Meta-Control Learning`
   - now treated as checkpoint-complete input, not the active lane
4. `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation`
   - now treated as checkpoint-complete input, not the active lane
5. `System-Level Learning / Feedback Integration`
   - now treated as checkpoint-complete input, not the active lane
6. `Research / Promotion Intelligence`
   - now treated as completed enough for first checkpoint and handoff
7. `Alpha / Strategy Selection Intelligence`
   - now treated as completed enough for first checkpoint and handoff
8. `Portfolio Intelligence`
   - now treated as completed enough for first checkpoint and handoff
9. `Governance -> Runtime Control`
   - now treated as completed enough for first checkpoint and handoff

## Current Recommendation

Use `SERI-01` as the current active task.

## Explicit Non-Tasks

These are not current tasks:

- replaying old hardening packet order
- creating another acceptance-only lane
- re-packaging resume docs again
- reopening `Phase1` to `Phase7` closure work
- deepening `Execution Reality`
- deepening `Governance -> Runtime Control`
- deepening `Portfolio Intelligence`
- deepening `Alpha / Strategy Selection Intelligence`
- deepening `Research / Promotion Intelligence`
- reopening `SLLFI` as the active packet lane
- reopening `Policy Optimization` as the active packet lane
- continuing `Live Capital Control` packet expansion as the active lane
- continuing `Meta Portfolio Intelligence` packet expansion as the active lane

## Inputs To Read Before Acting

1. `../00_index/README.md`
2. `../Cross_thread_resume_handover_2026-04-02.md`
3. `../PO_checkpoint_resume_memo_2026-04-04.md`
4. `../Policy_optimization_meta_control_learning_architect_status_update_2026-04-03.md`
5. `../Auto_resume_handover_2026-04-02.md`
6. `../Deployment_rollout_intelligence_checkpoint_v1.md`
7. `../Live_capital_control_adaptive_runtime_allocation_checkpoint_v1.md`
8. `../Meta_portfolio_intelligence_cross_strategy_capital_allocation_checkpoint_v1.md`

## Expected Output Of The Next Task

The current lane follow-up should produce:

- one packet plan doc
- one verifier script
- one regime-state surface

Current prerequisite lane output:

- `docs/Policy_optimization_meta_control_learning_packet01_plan.md`
- `test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet01.py`
- `docs/Policy_optimization_meta_control_learning_packet02_tuning_recommendations_plan.md`
- `test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet02_tuning_recommendations.py`
- `docs/Policy_optimization_meta_control_learning_packet03_persisted_meta_policy_state_plan.md`
- `test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet03_persisted_meta_policy_state.py`
- `docs/Policy_optimization_meta_control_learning_packet04_applied_tuning_consumption_plan.md`
- `test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet04_applied_tuning_consumption.py`
- `docs/Policy_optimization_meta_control_learning_packet05_outcome_effectiveness_plan.md`
- `test_bundle/scripts/verify_policy_optimization_meta_control_learning_packet05_outcome_effectiveness.py`
- `docs/Deployment_rollout_intelligence_packet01_plan.md`
- `test_bundle/scripts/verify_deployment_rollout_intelligence_packet01.py`
- `docs/Deployment_rollout_intelligence_packet02_candidate_docket_plan.md`
- `test_bundle/scripts/verify_deployment_rollout_intelligence_packet02_candidate_docket.py`
- `docs/Deployment_rollout_intelligence_packet03_persisted_rollout_state_plan.md`
- `test_bundle/scripts/verify_deployment_rollout_intelligence_packet03_persisted_rollout_state.py`
- `docs/Deployment_rollout_intelligence_packet04_applied_rollout_consumption_plan.md`
- `test_bundle/scripts/verify_deployment_rollout_intelligence_packet04_applied_rollout_consumption.py`
- `docs/Deployment_rollout_intelligence_packet05_rollout_outcome_effectiveness_plan.md`
- `test_bundle/scripts/verify_deployment_rollout_intelligence_packet05_rollout_outcome_effectiveness.py`
- `docs/Deployment_rollout_intelligence_checkpoint_v1.md`
- `docs/Live_capital_control_adaptive_runtime_allocation_packet01_plan.md`
- `test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet01.py`
- `docs/Live_capital_control_adaptive_runtime_allocation_packet02_adjustment_decision_plan.md`
- `test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet02_adjustment_decision.py`
- `docs/Live_capital_control_adaptive_runtime_allocation_packet03_control_state_plan.md`
- `test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet03_control_state.py`
- `docs/Live_capital_control_adaptive_runtime_allocation_packet04_control_consumption_plan.md`
- `test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet04_control_consumption.py`
- `docs/Live_capital_control_adaptive_runtime_allocation_packet05_control_effectiveness_plan.md`
- `test_bundle/scripts/verify_live_capital_control_adaptive_runtime_allocation_packet05_control_effectiveness.py`

## Single-Block Resume Note

```text
Current task is not another hardening packet, not another Execution Reality packet, not another Governance -> Runtime Control packet, not another Portfolio Intelligence packet, not another Alpha / Strategy Selection Intelligence packet, not another Research / Promotion Intelligence packet, not another active SLLFI packet, not another active Policy Optimization packet, not another active DRI packet, not another active LCC packet, and not another active MPI packet. Current task is `SERI-01` after `MPI-05` made cross-strategy capital efficiency explicit.
```
