# Sprint4 Integrated Working Directory

This document defines the **recommended working directory layout** for
Sprint4 real implementation. It integrates the uploaded source bundles
and establishes a clear separation between:

-   Source of Truth (reference code)
-   Integrated implementation code
-   Shared contracts and schemas
-   Infrastructure and tooling

Referenced bundles:

1.  v12_quantops_sprint3_production_realcode_bundle_prefixfixed_v2.zip
2.  V12_PhaseH_Sprint4_Quant_System_Bundle.zip
3.  V12_PhaseD_with_log.zip
4.  V8_Strategy_Engine_Bundle.zip

------------------------------------------------------------------------

# Top-Level Structure

    sprint4_real_impl/

    ├ README.md
    ├ .env.example
    ├ docker-compose.yml
    ├ Makefile

    ├ docs/
    │  ├ Sprint4_source_of_truth_mapping.md
    │  ├ Sprint4_real_implementation_tickets.md
    │  ├ integration_notes.md
    │  ├ api_contracts.md
    │  ├ db_schema_map.md
    │  └ migration_plan.md

    ├ source_of_truth/
    │  ├ quantops_sprint3/
    │  ├ v12_phaseh/
    │  ├ v12_phased/
    │  └ v8_strategy_reference/

    ├ apps/
    │  ├ quantops-api/
    │  ├ quantops-worker/
    │  └ v12-api/

    ├ shared/
    │  ├ schemas/
    │  ├ utils/
    │  └ contracts/

    ├ infra/
    │  ├ nginx/
    │  ├ scripts/
    │  └ compose/

    └ artifacts/
       ├ logs/
       ├ reports/
       └ snapshots/

------------------------------------------------------------------------

# Directory Responsibilities

## source_of_truth

Reference-only code extracted from uploaded bundles.

Purpose:

-   Preserve original implementations
-   Enable diff comparison
-   Prevent accidental modifications

Bundles placed here:

    quantops_sprint3/
    v12_phaseh/
    v12_phased/
    v8_strategy_reference/

------------------------------------------------------------------------

## apps/quantops-api

Control plane API responsible for:

-   dashboard
-   scheduler
-   monitoring
-   governance
-   alerts
-   approval workflows

Source of Truth:

    v12_quantops_sprint3_production_realcode_bundle_prefixfixed_v2

Core modules:

    api/routes/
    services/
    repositories/
    jobs/
    db/
    core/

------------------------------------------------------------------------

## apps/quantops-worker

Background services responsible for:

-   scheduler loop
-   cron engine
-   job execution
-   health monitoring
-   alert dispatch

Separating this from quantops-api improves runtime stability.

------------------------------------------------------------------------

## apps/v12-api

Runtime trading engine and portfolio system.

Responsible for:

-   portfolio engine
-   analytics engine
-   execution system
-   strategy runtime
-   orchestrator

Source of Truth:

Primary:

    V12_PhaseH_Sprint4_Quant_System_Bundle

Execution realism:

    V12_PhaseD_with_log

Core modules:

    portfolio/
    analytics/
    execution/
    orchestrator/
    strategy/
    services/
    repositories/
    api/routes/

------------------------------------------------------------------------

## shared

Shared contracts used across both systems.

Important components:

    schemas/api/
    schemas/db/
    events/
    contracts/

Defines:

-   API response shapes
-   DB schema mappings
-   event payload formats

------------------------------------------------------------------------

## infra

Infrastructure configuration.

    nginx/
    scripts/
    compose/

Includes:

-   docker compose stacks
-   helper scripts
-   deployment configs

------------------------------------------------------------------------

## artifacts

Generated files not tracked as source code.

Examples:

    logs/
    reports/
    snapshots/

------------------------------------------------------------------------

# Implementation Workflow

Recommended development flow:

1.  Extract all uploaded bundles into `source_of_truth/`
2.  Copy relevant modules into `apps/`
3.  Implement repository layer
4.  Replace mock endpoints with real implementations
5.  Implement analytics metrics
6.  Integrate scheduler jobs
7.  Finalize dashboard aggregation

------------------------------------------------------------------------

# Key Principle

**Never modify source_of_truth directly.**

Implementation should always happen inside:

    apps/
    shared/
    infra/

Source bundles remain immutable reference implementations.

------------------------------------------------------------------------

# Completion Criteria

Sprint4 integration is complete when:

-   Portfolio endpoints return real DB values
-   Analytics endpoints compute real metrics
-   Scheduler exposes real job state
-   Dashboard aggregates live services
-   Alerts and monitoring are functional
