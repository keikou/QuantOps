# Current Docs Migration Map

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `initial_mapping`

## Mapping Rule

This file maps the current flat `docs/` files to the proposed target structure.

It is a routing document first, not a move log.
Physical file moves should happen only after the target folder has a stable canonical entrypoint.

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
- `After_Sprint6H_Roadmap_from_Architect.md`
- `Development for AI.md`
- `chatgpt-codex-cowork.md`

Why:

- these explain project background, working assumptions, and collaboration context

## 02_architecture

- `architecture-read-models.md`
- `api-summary-contracts.md`
- `portfolio-display-semantics.md`
- `writer-observability.md`

Why:

- these are system structure, semantics, or model-shaping documents

## 03_plans

- `03_plans/README.md`
- `03_plans/current.md`
- `03_plans/roadmap.md`
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

Current gap:

- no dedicated task-spec set exists yet

Recommended first canonical files:

- `current.md`
- `active_tasks.md`
- `task_template.md`

Why:

- this is where AI-executable and human-readable task units should live next

## 05_workflows

- `development-workflow.md`
- `correlation-logging-guide.md`

Why:

- these describe repeatable flows and investigation paths

Current gap:

- `dev-flow`
- `incident-flow`
- `runtime-acceptance-flow`

should eventually exist as dedicated workflow docs

## 06_playbooks

- `timeout-improvement-pr-summary.md`
- `timeout-roadmap.md`

Why:

- these are closer to problem-solving and operational response than to core architecture

## 07_interfaces

- `api-summary-contracts.md`
- `portfolio-display-semantics.md`
- `architecture-read-models.md`

Candidate future additions:

- API schemas
- event contracts
- data contracts
- checkpoint payload shapes

Why:

- current interface documentation is thin and still partly embedded elsewhere

## 08_dev_guides

- `08_dev_guides/README.md`
- `08_dev_guides/current_dev_guide.md`
- `08_dev_guides/verification_guide.md`
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
- `ops-runbook.md`
- `correlation-logging-guide.md`
- `SprintH_completion_report.md`

Why:

- these are operational or runtime-observability-facing

## 10_agent

- `10_agent/README.md`
- `10_agent/system_context.md`
- `10_agent/rules.md`
- `10_agent/capabilities.md`
- `10_agent/constraints.md`
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

1. keep all current files where they are for now
2. add canonical `README.md` or `current.md` files in target folders gradually
3. move only high-signal entrypoint docs after replacement paths exist
4. create dedicated `04_tasks` and `05_workflows` content next

## Most Important Current Gaps

- no explicit `04_tasks/` layer yet
- no dedicated `05_workflows/` folder yet
- `07_interfaces/` is still too thin
- some docs belong to multiple views, so canonical ownership needs to be decided before moving files
