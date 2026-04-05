# Current Docs Migration Map

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `canonical_entrypoints_extended_across_context_plans_workflows_guides_agent_reports`

## Mapping Rule

This file maps the current flat `docs/` files to the proposed target structure.

It is a routing document first, and now also tracks the highest-signal moves already completed.
Physical file moves should still happen only after the target folder has a stable canonical entrypoint.

## 00_index

- `Auto_resume_handover_2026-04-02.md`
- `Architect_alignment_resume_memo_2026-04-02.md`
- `Resume_bundle_index_2026-04-02.md`
- `Resume_operator_packet_latest.md`

Why:

- these are current entrypoint and navigation artifacts

## 01_context

- `01_context/README.md`
- `01_context/project_state.md`
- `01_context/working_assumptions.md`
- `01_context/supporting_context_docs.md`
- `After_Sprint6H_Roadmap_from_Architect.md`
- `Development for AI.md`
- `chatgpt-codex-cowork.md`

Why:

- these explain project background, working assumptions, and collaboration context

## 02_architecture

- `02_architecture/README.md`
- `02_architecture/current_architecture.md`
- `02_architecture/system_overview.md`
- `02_architecture/architecture_layers.md`
- `02_architecture/system_ownership_map.md`
- `02_architecture/components.md`
- `02_architecture/data_flow.md`
- `02_architecture/QuantOps_Architecture_Master.md`
- `02_architecture/V12_Architecture_Master.md`
- `02_architecture/architecture-read-models.md`
- `02_architecture/writer-observability.md`

Why:

- these are system structure and model-shaping documents

## 03_plans

- `03_plans/README.md`
- `03_plans/current.md`
- `03_plans/roadmap.md`
- `03_plans/historical_plans.md`
- `sprinth-finish-plan.md`
- `Post_Phase7_hardening_plan.md`
- `Phase2_execution_closure_plan.md`
- `Phase3_allocation_closure_plan.md`
- `Phase4_alpha_factory_plan.md`
- `Phase5_risk_guard_plan.md`
- `Phase6_live_trading_plan.md`
- `Phase7_self_improving_system_plan.md`
- `Recovery_replay_confidence_plan.md`
- `Cross_phase_acceptance_plan.md`
- `Audit_provenance_gap_review.md`
- `Audit_provenance_mirroring_plan.md`
- `Audit_governance_mirroring_plan.md`
- `Runtime_config_provenance_plan.md`
- `Deploy_provenance_plan.md`
- `Runtime_governance_linkage_plan.md`
- `Multi_cycle_acceptance_plan.md`
- `Operator_diagnostic_bundle_plan.md`
- `Recovery_replay_diagnostic_bundle_plan.md`
- `Hardening_status_surface_plan.md`
- `Hardening_evidence_snapshot_plan.md`
- `Hardening_architect_handoff_plan.md`
- `Hardening_handover_manifest_plan.md`
- `Resume_automation_helper_plan.md`
- `Resume_bundle_index_plan.md`
- `Resume_operator_packet_plan.md`
- `Resume_quickcheck_runner_plan.md`
- `Resume_bundle_refresh_runner_plan.md`
- `Resume_command_index_update_plan.md`
- `Resume_bundle_completion_status_plan.md`

Why:

- these are plan, packet, or migration-intent documents

## 04_tasks

- `04_tasks/current.md`
- `04_tasks/active_tasks.md`
- `04_tasks/task_template.md`
- `04_tasks/README.md`
- `04_tasks/task_generation_rules.md`
- `04_tasks/runtime_regression_verification_task.md`
- `04_tasks/contract_doc_update_task.md`
- `04_tasks/docs_route_sync_task.md`
- `04_tasks/docs_first_execution_prep_task.md`
- `04_tasks/interface_contract_hardening_2026-04-05.md`
- `04_tasks/seri01_regime_detection_and_strategy_gating_engine_2026-04-05.md`

Why:

- this is the canonical task-spec layer for AI-executable and human-readable task units

## 05_workflows

- `05_workflows/README.md`
- `05_workflows/dev-flow.md`
- `05_workflows/incident-flow.md`
- `05_workflows/runtime-acceptance-flow.md`
- `05_workflows/supporting_workflows.md`
- `development-workflow.md`
- `correlation-logging-guide.md`

Why:

- these describe repeatable flows and investigation paths

## 06_playbooks

- `06_playbooks/timeout-improvement-pr-summary.md`
- `06_playbooks/timeout-roadmap.md`
- `06_playbooks/README.md`
- `06_playbooks/current_playbooks.md`
- `06_playbooks/runtime_regression_triage.md`
- `06_playbooks/resume_and_docs_state_drift.md`
- `06_playbooks/api_failure_triage.md`
- `06_playbooks/rollback_decision_path.md`

Why:

- these are closer to problem-solving and operational response than to core architecture

## 07_interfaces

- `07_interfaces/V12_QuantOps_Interface_Contract.md`
- `07_interfaces/api-summary-contracts.md`
- `07_interfaces/portfolio-display-semantics.md`
- `07_interfaces/README.md`
- `07_interfaces/current_contracts.md`
- `07_interfaces/event_contracts.md`
- `07_interfaces/runtime_checkpoint_shapes.md`
- `07_interfaces/operator_bundle_payloads.md`
- `07_interfaces/endpoint_contract_matrix.md`
- `07_interfaces/lane_surface_inventory.md`
- `07_interfaces/api_endpoints.md`
- `07_interfaces/data_schema.md`
- `07_interfaces/runtime_payloads.md`
- `07_interfaces/seri_regime_adaptation_contracts.md`
- `02_architecture/architecture-read-models.md`

Why:

- current interface documentation now has a canonical folder route, but physical ownership is still mixed between `07_interfaces/` and a few adjacent docs

## 08_dev_guides

- `08_dev_guides/README.md`
- `08_dev_guides/current_dev_guide.md`
- `08_dev_guides/verification_guide.md`
- `08_dev_guides/supporting_guides.md`
- `development-rules-v12-vs-quantops.md`
- `development-workflow.md`
- `dev-startup.md`
- `ci_regression_packs.md`

Why:

- these are implementation and contributor guides

## 09_runtime_ops

- `09_runtime_ops/README.md`
- `09_runtime_ops/current_runtime_ops.md`
- `09_runtime_ops/incident_and_tracing.md`
- `09_runtime_ops/supporting_runtime_ops.md`
- `ops-runbook.md`
- `correlation-logging-guide.md`
- `SprintH_completion_report.md`

Why:

- these are operational or runtime-observability-facing

## 10_agent

- `10_agent/README.md`
- `10_agent/ai_docs_operating_loop.md`
- `10_agent/system_context.md`
- `10_agent/rules.md`
- `10_agent/capabilities.md`
- `10_agent/constraints.md`
- `10_agent/supporting_agent_docs.md`
- `Development for AI.md`
- `chatgpt-codex-cowork.md`
- `Architect_alignment_resume_memo_2026-04-02.md`

Why:

- these directly shape agent behavior, resume behavior, or AI collaboration

## 11_reports

- `11_reports/README.md`
- `11_reports/current_status.md`
- `11_reports/historical_reports.md`
- `Sprint6H_truth_completion_final.md`
- `Phase2_execution_completion_final.md`
- `Phase3_allocation_completion_final.md`
- `Phase4_alpha_factory_completion_final.md`
- `Phase5_risk_guard_completion_final.md`
- `Phase6_live_trading_completion_final.md`
- `Phase7_self_improving_completion_final.md`
- `Phase2_phase3_status_for_architect.md`
- `Phase3_allocation_status_for_architect.md`
- `Phase3_allocation_status_update.md`
- `Phase4_status_for_architect.md`
- `Phase4_status_update.md`
- `Phase5_status_for_architect.md`
- `Phase5_status_update.md`
- `Phase6_status_for_architect.md`
- `Phase6_status_update.md`
- `Phase7_status_for_architect.md`
- `Phase7_status_update.md`
- `Post_Phase7_hardening_status_for_architect.md`
- `Post_Phase7_hardening_status_update.md`
- `Post_Phase7_hardening_status_update_2026-04-01.md`
- `Post_Phase7_hardening_architect_report_2026-04-02.md`
- `Hardening_architect_handoff_latest.md`
- `Resume_bundle_completion_status_2026-04-02.md`
- `V12_truth_completion_reply_for_architect.md`
- `V12_truth_completion_review_for_architect.md`

Why:

- these capture state, progress, architect-facing summaries, and historical completion evidence

## 99_archive

Archive candidates should be chosen later.
Do not archive anything just because it is old.

Archive only when:

- a newer canonical replacement exists
- inbound references have been updated
- the file is historical rather than operational

## Recommended Next Migration Steps

1. verify the expanded canonical entrypoints stay internally consistent
2. continue routing root-level docs through folder-owned `README.md` or `current.md` files before physical moves
3. keep the docs-first AI operating loop visible from `00_index` and `10_agent`
4. keep `SERI-01` visible as a docs-ready lane before code implementation starts
5. decide the next high-signal physical moves only after ownership is stable
6. use verifier coverage to catch stale docs-state drift early

## Most Important Current Gaps

- root-level plan and report artifacts still remain physically outside their canonical folders
- root-level workflow and guide docs still remain physically outside their canonical folders
- some docs still belong to multiple views, so canonical ownership needs to be decided before moving more files
- the docs-only AI operating loop is now defined, but downstream folder entrypoints should continue to reference it consistently
- `SERI` implementation docs are prepared, but the code surface itself is not implemented yet
