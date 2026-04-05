# Verification Guide

Date: `2026-04-02`
Repo: `QuantOps_github`
Status: `current_verification_guidance`

## Purpose

This file explains how to choose the right verification depth for implementation work.

## Verification Order

1. derive the current verifier path from docs first
2. run the narrowest relevant verifier first
3. run startup or integration checks only when the task actually touches them
4. prefer repo-local proof over conversational confidence

## Current High-Signal Checks

Startup and local stack:

- `../dev-startup.md`
- `powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_local_startup_smoke.ps1`

QuantOps regression surface:

- `../ci_regression_packs.md`
- `powershell -ExecutionPolicy Bypass -File test_bundle/scripts/run_quantops_api_regression_pack.ps1 -Pack all`

Resume and handover checks:

- `python test_bundle/scripts/run_resume_quickcheck.py --json`
- `python test_bundle/scripts/run_resume_bundle_refresh.py --json`
- `python test_bundle/scripts/resume_hardening_helper.py --json`

Docs-structure checks added in this lane:

- `python test_bundle/scripts/verify_docs_structure_index.py`
- `python test_bundle/scripts/verify_tasks_and_workflows_docs.py`
- `python test_bundle/scripts/verify_interfaces_docs.py`
- `python test_bundle/scripts/verify_plans_docs.py`
- `python test_bundle/scripts/verify_context_docs.py`
- `python test_bundle/scripts/verify_reports_docs.py`
- `python test_bundle/scripts/verify_dev_guides_docs.py`
- `python test_bundle/scripts/verify_agent_docs.py`

## Rule

A task is not complete just because the code change looks coherent.

At minimum:

- the verifier path should be explainable from current docs
- the smallest relevant verifier should pass
- the docs entrypoint for future threads should remain accurate

## Current Non-Goal

Do not run broad verification just to re-prove already completed hardening packets unless the current task actually touches them.
