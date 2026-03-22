# Integration Manifest

## apps/quantops-api
Copied from:
- Sprint3 production real code bundle (`services/quantops-api`)

## apps/v12-api
Copied from:
- PhaseH Sprint4 Quant System bundle (`ai_hedge_bot`, `db`)
Overlaid with:
- PhaseD execution files (`ai_hedge_bot/execution/*`)
- PhaseD execution services (`execution_service.py`, `execution_intent_service.py`)

## apps/quantops-worker
Derived from:
- Sprint3 `app/worker.py`
Additional placeholders added:
- `scheduler.py`
- `job_registry.py`
- `cron_engine.py`

## Reference-only
- V8 strategy source placed in `source_of_truth/v8_strategy_reference` and `apps/v12-api/_strategy_reference_v8`
