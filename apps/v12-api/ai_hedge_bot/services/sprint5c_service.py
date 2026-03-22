from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from ai_hedge_bot.analytics.alpha_metrics import AlphaMetricsEngine
from ai_hedge_bot.analytics.performance_engine import PerformanceEngine
from ai_hedge_bot.core.config import AppConfig
from ai_hedge_bot.governance.kill_switch import KillSwitch
from ai_hedge_bot.governance.regime_switch import RegimeSwitchEngine
from ai_hedge_bot.governance.strategy_budget_allocator import StrategyBudgetAllocator
from ai_hedge_bot.risk.risk_engine import RiskEngine
from ai_hedge_bot.services.sprint5c_store import Sprint5CStore


class Sprint5CService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.store = Sprint5CStore(config.data_db_path)
        self.risk_engine = RiskEngine()
        self.performance_engine = PerformanceEngine()
        self.alpha_metrics_engine = AlphaMetricsEngine()
        self.strategy_budget_allocator = StrategyBudgetAllocator()
        self.regime_switch_engine = RegimeSwitchEngine()
        self.kill_switch = KillSwitch()

    def run_once(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        run_id = str(payload.get('run_id', f's5c_{datetime.now(UTC).strftime("%Y%m%dT%H%M%S")}'))
        created_at = datetime.now(UTC).isoformat()
        positions = list(payload.get('positions', []))
        current_equity = float(payload.get('current_equity', 100000.0))
        previous_peak_equity = float(payload.get('previous_peak_equity', current_equity))

        risk_snapshot = self.risk_engine.evaluate_portfolio_risk(
            run_id=run_id,
            positions=positions,
            current_equity=current_equity,
            previous_peak_equity=previous_peak_equity,
        )
        self.store.insert_risk_snapshot(risk_snapshot.to_dict())

        perf = self.performance_engine
        performance_snapshot = {
            'run_id': run_id,
            'created_at': created_at,
            'daily_return': perf.calculate_daily_return(float(payload.get('previous_equity', current_equity)), current_equity),
            'cumulative_return': perf.calculate_cum_return(list(payload.get('return_history', []))),
            'volatility': perf.calculate_volatility(list(payload.get('return_history', []))),
            'sharpe': perf.calculate_sharpe(list(payload.get('return_history', []))),
            'sortino': perf.calculate_sortino(list(payload.get('return_history', []))),
            'max_drawdown': perf.calculate_max_drawdown(list(payload.get('equity_curve', [current_equity]))),
            'turnover': perf.calculate_turnover(dict(payload.get('previous_weights', {})), dict(payload.get('current_weights', {}))),
        }
        self.store.insert_performance_snapshot(performance_snapshot)

        alpha_snapshot = self.alpha_metrics_engine.build_snapshot(
            run_id=run_id,
            signal_values=list(payload.get('signal_values', [])),
            forward_returns=list(payload.get('forward_returns', [])),
            ic_history=list(payload.get('ic_history', [])),
            previous_signals=dict(payload.get('previous_signals', {})),
            current_signals=dict(payload.get('current_signals', {})),
            candidate_count=int(payload.get('candidate_count', 0)),
        )
        self.store.insert_alpha_metrics_snapshot(alpha_snapshot.to_dict())

        budgets = self.strategy_budget_allocator.allocate_strategy_risk_budget(list(payload.get('strategy_stats', [])))
        self.store.insert_strategy_risk_budgets(run_id, created_at, budgets)

        regime = self.regime_switch_engine.detect_regime(
            volatility=float(risk_snapshot.portfolio_volatility),
            correlation=float(payload.get('avg_cross_asset_correlation', 0.0)),
            trend_score=float(payload.get('trend_score', 0.0)),
        )
        self.store.insert_regime_state(run_id, created_at, regime.to_dict())

        kill_switch = self.kill_switch.trigger_kill_switch(risk_snapshot.to_dict())
        return {
            'run_id': run_id,
            'risk': risk_snapshot.to_dict(),
            'performance': performance_snapshot,
            'alpha_metrics': alpha_snapshot.to_dict(),
            'strategy_budgets': budgets,
            'regime': regime.to_dict(),
            'kill_switch': kill_switch,
        }

    def get_latest_risk(self) -> dict[str, Any]:
        return self.store.latest_risk()

    def get_risk_history(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.store.risk_history(limit=limit)

    def get_latest_performance(self) -> dict[str, Any]:
        return self.store.latest_performance()

    def get_latest_alpha_metrics(self) -> dict[str, Any]:
        return self.store.latest_alpha_metrics()

    def get_latest_budgets(self) -> list[dict[str, Any]]:
        return self.store.latest_budgets()

    def get_latest_regime(self) -> dict[str, Any]:
        return self.store.latest_regime()
