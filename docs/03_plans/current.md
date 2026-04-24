# Current Plan

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Status: `aes04_active_boundary`

## Current Planning Decision

The current hardening/resume slice is treated as sufficiently complete.

So the active planning question is now:

- how should generated alpha be evaluated before promotion?
- how should noise, decay, overfit, and redundancy become explicit at the system surface?
- how should selection decisions become operator-visible before portfolio intake?

Historical note:

- `Execution Reality` was the earliest next-lane candidate after hardening/resume, but it is no longer the current active planning answer

## Current Answer

Architect-selected answer:

- `Strategy Evolution / Regime Adaptation Intelligence v1` is checkpoint-complete through `SERI-05`
- `Autonomous Alpha Expansion / Strategy Generation Intelligence v1` is checkpoint-complete through `AAE-05`
- `Autonomous Alpha Expansion / Strategy Generation Intelligence v1` is checkpoint-complete through `AAE-05`
- `Alpha Synthesis / Structural Discovery Intelligence v1` is checkpoint-complete through `ASD-05`
- next top-level lane is `Alpha Evaluation / Selection Intelligence`
- current packet boundary is `AES-04: Economic Meaning / Factor Attribution`

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
- `Deployment / Rollout Intelligence v1`
- `Live Capital Control / Adaptive Runtime Allocation v1`
- `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1`
- `Strategy Evolution / Regime Adaptation Intelligence v1`

That means planning should not continue replaying `SERI`, `AAE`, or `ASD` checkpoint work and should now establish the first robust alpha evaluation gate.

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
10. complete `Policy Optimization / Meta-Control Learning v1` through `PO-05`
11. complete `Deployment / Rollout Intelligence v1` through `DRI-05`
12. complete `Live Capital Control / Adaptive Runtime Allocation v1` through `LCC-05`
13. complete `Meta Portfolio Intelligence / Cross-Strategy Capital Allocation v1` through `MPI-05`
14. complete `Strategy Evolution / Regime Adaptation Intelligence v1` through `SERI-05`

## Current Plan Outputs

Current `AES-04` outputs now planned:

- `../Alpha_evaluation_selection_intelligence_packet04_plan.md`
- `../../test_bundle/scripts/verify_alpha_evaluation_selection_intelligence_packet04.py`
- `POST /system/alpha-factor-attribution/run`
- `GET /system/alpha-factor-attribution/latest`
- `GET /system/alpha-factor-attribution/candidate/{alpha_id}`
- `GET /system/alpha-factor-exposure/latest`
- `GET /system/alpha-residual-alpha/latest`
- `GET /system/alpha-economic-risk/latest`
- `GET /system/alpha-factor-concentration/latest`
- `GET /system/alpha-economic-meaning/latest`
- `GET /system/alpha-factor-attribution/ensemble/{ensemble_id}`

## Current Docs-Ready State

The docs route for `AES-04` is now prepared for implementation startup.

Current docs-ready assets:

- `../04_tasks/aes04_economic_meaning_factor_attribution_2026-04-25.md`
- `../AES-01_GitHub_Issues.md`
- `../AES_Threshold_Tuning_Strategy.md`
- `../AES-02_Walk_Forward_Validation_Design.md`
- `../AES-03_Alpha_Ensemble_Selection_Engine_Design.md`
- `../AES-03_GitHub_Issues_Implementation.md`
- `../AES-03_Weight_Optimization_Algorithms.md`
- `../AES-03_Portfolio_Integration_MPI_LCC.md`
- `../AES-04_Economic_Meaning_Factor_Attribution_Design.md`
- `../AES-05_Capacity_Crowding_Risk_Engine.md`
- `../AES-06_Dynamic_Alpha_Weighting_Engine.md`
- `../AES-07_Alpha_Kill_Switch_Retirement_Engine.md`
- `../AES-08_Self_Improving_Alpha_Loop.md`
- `../07_interfaces/aes_alpha_evaluation_contracts.md`
- `../07_interfaces/lane_surface_inventory.md`
- `../10_agent/ai_docs_operating_loop.md`

## Non-Plan

This is not the current plan:

- another hardening-only lane
- another resume packaging lane
- another acceptance restart
- another `Execution Reality` expansion
- replaying completed `DRI`, `LCC`, `MPI`, or `SERI` packets
- inventing `SERI-06`
- replaying completed `AAE-01` through `AAE-05`
- replaying completed `ASD-01` through `ASD-05`
- inventing `ASD-06` without a new architect boundary
- replaying completed `AAE` or `ASD` work instead of building the next `AES` packet

## Read Before Editing

1. `../Cross_thread_resume_handover_2026-04-24.md`
2. `../Auto_resume_handover_2026-04-24.md`
3. `../04_tasks/current.md`
4. `../Autonomous_alpha_expansion_strategy_generation_intelligence_packet01_plan.md`
5. `./roadmap.md`
