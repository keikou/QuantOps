# Sprint4 Source of Truth Mapping

This document defines which uploaded ZIP bundle and which files should
be treated as the **Source of Truth (SoT)** when implementing Sprint4
real‑implementation.

Uploaded bundles referenced:

1.  v12_quantops_sprint3_production_realcode_bundle_prefixfixed_v2.zip
2.  V12_PhaseH_Sprint4_Quant_System_Bundle.zip
3.  V12_PhaseD_with_log.zip
4.  V8_Strategy_Engine_Bundle.zip

------------------------------------------------------------------------

# Global Rule

## Control Plane

QuantOps infrastructure and control APIs.

Source of Truth:
v12_quantops_sprint3_production_realcode_bundle_prefixfixed_v2.zip

## Runtime Plane

Trading runtime, portfolio engine, analytics, orchestrator.

Source of Truth: V12_PhaseH_Sprint4_Quant_System_Bundle.zip

## Execution Realism

Fill simulation, shadow execution, cost model.

Source of Truth: V12_PhaseD_with_log.zip

## Strategy Concept Reference

Strategy architecture reference implementation.

Source of Truth: V8_Strategy_Engine_Bundle.zip

------------------------------------------------------------------------

# Mapping Table

  ------------------------------------------------------------------------------------------
  Domain            Source ZIP        Key Files                            Notes
  ----------------- ----------------- ------------------------------------ -----------------
  QuantOps API      Sprint3 bundle    services/quantops-api/app/main.py    Primary control
                                                                           API

  QuantOps Routes   Sprint3 bundle    app/api/routes/dashboard.py,         API surface
                                      scheduler.py, risk.py                

  QuantOps Services Sprint3 bundle    app/services/dashboard_service.py,   Business logic
                                      scheduler_service.py                 

  QuantOps          Sprint3 bundle    app/repositories/duckdb.py           DB access
  Repositories                                                             

  QuantOps Jobs     Sprint3 bundle    app/jobs/risk_snapshot_job.py        Scheduler jobs

  QuantOps          Sprint3 bundle    app/db/migrations/\*.sql             Control DB schema
  Migrations                                                               

  V12 API Routes    PhaseH bundle     api/routes/portfolio.py,             Runtime API
                                      analytics.py                         

  Portfolio Engine  PhaseH bundle     portfolio/portfolio_engine.py        Portfolio runtime

  Portfolio         PhaseH bundle     portfolio/optimizer.py               Allocation
  Optimizer                                                                

  Portfolio Risk    PhaseH bundle     portfolio/risk_model.py              Risk metrics
  Model                                                                    

  Orchestrator      PhaseH bundle     orchestrator/cycle_runner.py         Runtime cycle

  Analytics         PhaseH bundle     analytics/analytics_service.py       Metrics

  Execution Core    PhaseD bundle     execution/shadow_engine.py           Execution realism

  Fill Simulation   PhaseD bundle     execution/fill_simulator.py          Fill model

  Cost Model        PhaseD bundle     execution/cost_model.py              Fee + slippage

  Strategy Runtime  PhaseH bundle     strategy/strategy_runtime.py         Strategy runtime

  Strategy Registry PhaseH bundle     strategy/strategy_registry.py        Strategy catalog

  Capital Allocator PhaseH bundle     strategy/capital_allocator.py        Capital
                                                                           distribution

  Strategy          V8 bundle         src/strategy/\*.py                   Concept reference
  Reference                                                                
  ------------------------------------------------------------------------------------------

------------------------------------------------------------------------

# Ticket Mapping

## TICKET-001 / TICKET-002

Database connection and BaseRepository.

Source: Sprint3 QuantOps bundle

Key Files:

app/repositories/duckdb.py\
app/db/migrations/\*.sql

------------------------------------------------------------------------

## TICKET-003 -- TICKET-006

Portfolio real implementation.

Source: PhaseH bundle

Key Files:

portfolio/portfolio_engine.py\
portfolio/optimizer.py\
portfolio/risk_model.py

------------------------------------------------------------------------

## TICKET-007 -- TICKET-012

Analytics real implementation.

Source: PhaseH bundle

Key Files:

analytics/analytics_service.py\
analytics/portfolio_analytics.py\
analytics/execution_analytics.py

Supplement:

PhaseD execution logs

------------------------------------------------------------------------

## TICKET-013 -- TICKET-016

Scheduler and runner.

Source: Sprint3 QuantOps bundle

Key Files:

app/jobs/\*.py\
app/services/scheduler_service.py\
app/repositories/scheduler_repository.py

------------------------------------------------------------------------

## TICKET-017 -- TICKET-018

Dashboard aggregation.

Source: Sprint3 QuantOps bundle

Key Files:

app/services/dashboard_service.py

------------------------------------------------------------------------

## TICKET-019 -- TICKET-020

Alerts and notifier.

Source: Sprint3 QuantOps bundle

Key Files:

app/services/alert_service.py\
app/repositories/alert_repository.py

------------------------------------------------------------------------

# Directory Layout Recommendation

Recommended working layout when implementing Sprint4:

source_of_truth/

quantops/ (Sprint3 bundle)

v12_runtime/ (PhaseH bundle)

execution_engine/ (PhaseD bundle)

strategy_reference/ (V8 bundle)

------------------------------------------------------------------------

# Implementation Priority

1.  QuantOps repository layer
2.  Portfolio real data
3.  Analytics real metrics
4.  Scheduler job persistence
5.  Dashboard aggregation
6.  Alerts and notifier

------------------------------------------------------------------------

# Completion Criteria

Sprint4 real implementation is considered complete when:

-   Portfolio endpoints return real DB values
-   Analytics endpoints return calculated metrics
-   Scheduler exposes real job state
-   Dashboard aggregates real services
-   Mock responses are removed
