# Current Tasks

Date: `2026-04-24`
Repo: `QuantOps_github`
Branch: `codex/post-phase7-hardening`
Track: `operational_risk_control_intelligence`
Status: `orc05_active`

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

- establish `Operational Risk & Control Intelligence`
- implement `ORC-05: Incident Audit / Operator Governance Bridge`

Current architect-selected candidate:

- `Operational Risk & Control Intelligence`
- current implementation boundary = `ORC-05`
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
- current dependency 11 = `Strategy Evolution / Regime Adaptation Intelligence v1 checkpoint through SERI-05`

## Why This Is The Active Task

Architect now treats `Strategy Evolution / Regime Adaptation Intelligence v1` as checkpoint-complete.

The next question is:

- "can operational incidents be governance-visible?"
- "can high-risk responses create approval-ready payloads?"
- "can audit, dispatch, override, and recovery governance be staged before AFG exists?"

This is the next lane beyond the completed hardening/resume slice, but it is no longer the older `Execution Reality` default.

## Next Candidate Options

1. `Alpha Evaluation / Selection Intelligence`
   - selected as the next top-level lane from the current repo truth
2. `Alpha Synthesis / Structural Discovery Intelligence`
   - now treated as checkpoint-complete input, not the active lane
3. `Autonomous Alpha Expansion / Strategy Generation Intelligence`
   - now treated as checkpoint-complete input, not the active lane
4. `Strategy Evolution / Regime Adaptation Intelligence`
   - now treated as checkpoint-complete input, not the active lane
5. `Deployment / Rollout Intelligence`
   - now treated as checkpoint-complete input, not the active lane
6. `Live Capital Control / Adaptive Runtime Allocation`
   - now treated as checkpoint-complete input, not the active lane

## Current Recommendation

Use `ORC-05` as the current active task.

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
- continuing `DRI`, `LCC`, `MPI`, or `SERI` packet expansion as the active lane
- replaying `AAE-01` through `AAE-05` without a real regression
- extending `AAE` to fake generator-core completion
- replaying `ASD-01` through `ASD-05` without a real regression
- inventing `ASD-06` before next-lane reselection
- using portfolio allocation as a substitute for alpha evaluation

## Inputs To Read Before Acting

1. `../00_index/README.md`
2. `../Cross_thread_resume_handover_2026-04-24.md`
3. `../Auto_resume_handover_2026-04-24.md`
4. `../Autonomous_alpha_expansion_strategy_generation_intelligence_checkpoint_v1.md`
5. `../Alpha_synthesis_structural_discovery_intelligence_checkpoint_v1.md`
6. `../AES-01_GitHub_Issues.md`
7. `../AES_Threshold_Tuning_Strategy.md`
8. `../AES-02_Walk_Forward_Validation_Design.md`
9. `../AES-03_Alpha_Ensemble_Selection_Engine_Design.md`
10. `../AES-03_GitHub_Issues_Implementation.md`
11. `../AES-03_Weight_Optimization_Algorithms.md`
12. `../AES-03_Portfolio_Integration_MPI_LCC.md`
13. `../AES-04_Economic_Meaning_Factor_Attribution_Design.md`
14. `../AES-05_Capacity_Crowding_Risk_Engine.md`
15. `../AES-06_Dynamic_Alpha_Weighting_Engine.md`
16. `../AES-07_Alpha_Kill_Switch_Retirement_Engine.md`
17. `../AES-08_Self_Improving_Alpha_Loop.md`
18. `../07_interfaces/aes_alpha_evaluation_contracts.md`

## Expected Output Of The Next Task

The current lane follow-up should produce:

- one packet plan doc
- one verifier script
- governance incident, pending approval, audit, dispatch, override-sync, and recovery governance surfaces

Current `ORC-05` outputs now planned:

- `docs/Operational_risk_control_intelligence_packet05_plan.md`
- `test_bundle/scripts/verify_operational_risk_control_intelligence_packet05.py`
- `POST /system/orc-governance/sync`
- `GET /system/orc-governance/latest`
- `GET /system/orc-governance/incidents/latest`
- `GET /system/orc-governance/incident/{incident_id}`
- `GET /system/orc-governance/pending-approvals/latest`
- `GET /system/orc-governance/audit/latest`
- `POST /system/orc-governance/recovery/request`
- `GET /system/orc-governance/recovery/latest`

## Single-Block Resume Note

```text
Current task is not another hardening packet, not another Execution Reality packet, not another Governance -> Runtime Control packet, not another Portfolio Intelligence packet, not another Alpha / Strategy Selection Intelligence packet, not another Research / Promotion Intelligence packet, and not another active DRI, LCC, MPI, SERI, AAE, ASD, or AES packet. Current task is `ORC-05`, so completed `AES-01` through `AES-08` and `ORC-01` through `ORC-04` work should be treated as input lanes and not replayed unless a real regression is found.
```
