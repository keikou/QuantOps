from __future__ import annotations

from fastapi import FastAPI
from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.features.feature_pipeline import FeaturePipeline
from ai_hedge_bot.alpha.alpha_registry import ALPHA_REGISTRY
from ai_hedge_bot.services.trading_service import TradingService
from ai_hedge_bot.analytics.alpha_analytics import load_alpha_performance
from ai_hedge_bot.analytics.regime_analytics import load_regime_performance
from ai_hedge_bot.analytics.portfolio_analytics import load_portfolio_diagnostics
from ai_hedge_bot.analytics.weight_analytics import load_weight_history
from ai_hedge_bot.analytics.portfolio_phasec_analytics import (
    load_expected_returns,
    load_paper_pnl,
    load_portfolio_allocations,
    load_portfolio_risk,
    load_portfolio_summary,
    load_portfolio_weights,
)
from ai_hedge_bot.orchestration.paper_runner import ContinuousPaperRunner
from ai_hedge_bot.services.execution_service import ExecutionAnalyticsService

app = FastAPI(title='AI Hedge Bot V12 Phase C Quant System', version='0.4.0')
service = TradingService()
store = service.analytics.store
runner = ContinuousPaperRunner(service, SETTINGS.runtime_dir / 'paper_runner_state.json')
execution_analytics = ExecutionAnalyticsService(store)

@app.get('/health')
def health():
    return {'status': 'ok', 'mode': SETTINGS.mode, 'symbols': SETTINGS.symbols, 'phase': 'D'}

@app.post('/run-once')
def run_once():
    return service.run_once()

@app.post('/runner/run-cycle')
def runner_run_cycle():
    return runner.run_cycle()

@app.get('/runner/status')
def runner_status():
    return runner.load_state()

@app.get('/weights')
def weights():
    return service.weight_store.load()

@app.get('/positions')
def positions():
    return [vars(p) for p in service.executor.positions.values()]

@app.get('/features/schema')
def features_schema():
    return {'count': len(FeaturePipeline.FEATURE_SCHEMA), 'features': FeaturePipeline.FEATURE_SCHEMA}

@app.get('/alpha/registry')
def alpha_registry():
    return {'count': len(ALPHA_REGISTRY), 'alphas': list(ALPHA_REGISTRY.keys())}

@app.get('/analytics/alpha-performance')
def alpha_performance():
    return load_alpha_performance(store)

@app.get('/analytics/regime-performance')
def regime_performance():
    return load_regime_performance(store)

@app.get('/analytics/portfolio-diagnostics')
def portfolio_diagnostics():
    return load_portfolio_diagnostics(store)

@app.get('/analytics/weight-history')
def weight_history():
    return load_weight_history(store)

@app.post('/analytics/rebuild')
def rebuild():
    return service.analytics.rebuild()

@app.get('/portfolio/expected-returns')
def portfolio_expected_returns():
    return load_expected_returns(store)

@app.get('/portfolio/weights')
def portfolio_weights():
    return load_portfolio_weights(store)

@app.get('/portfolio/allocations')
def portfolio_allocations():
    return load_portfolio_allocations(store)

@app.get('/portfolio/risk')
def portfolio_risk():
    return load_portfolio_risk(store)

@app.get('/portfolio/summary')
def portfolio_summary():
    return load_portfolio_summary(store)

@app.get('/portfolio/paper-pnl')
def paper_pnl():
    return load_paper_pnl(store)

@app.get('/analytics/shadow-summary')
def shadow_summary():
    return execution_analytics.shadow_summary()

@app.get('/analytics/execution-quality')
def execution_quality():
    return execution_analytics.execution_quality()

@app.get('/analytics/slippage-report')
def slippage_report():
    return execution_analytics.slippage_report()

@app.get('/analytics/order-lifecycle')
def order_lifecycle():
    return execution_analytics.order_lifecycle()

@app.get('/execution/shadow-orders')
def shadow_orders():
    return execution_analytics.shadow_orders()

@app.get('/execution/shadow-fills')
def shadow_fills():
    return execution_analytics.shadow_fills()

@app.get('/execution/latency')
def execution_latency():
    return execution_analytics.latency()
