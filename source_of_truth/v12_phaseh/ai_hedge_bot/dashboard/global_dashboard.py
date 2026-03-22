from __future__ import annotations

from ai_hedge_bot.analytics.analytics_service import AnalyticsService
from ai_hedge_bot.analytics.strategy_analytics import StrategyAnalytics
from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService


def build() -> dict:
    service = AnalyticsService()
    signal = service.signal_summary()
    portfolio = service.portfolio_summary()
    execution = service.execution_quality()
    strategy = StrategyAnalytics().summary()
    alpha = AutonomousAlphaService().overview()
    return {
        'dashboard': 'global',
        'status': 'ok',
        'cards': {
            'signal_count': signal.get('signal_count', signal.get('signals_evaluated', 0)),
            'portfolio_count': portfolio.get('portfolio_count', 0),
            'fill_rate': execution.get('fill_rate'),
            'strategy_count': strategy.get('aggregate', {}).get('strategy_count', 0),
            'allocated_capital': strategy.get('aggregate', {}).get('allocated_capital', 0.0),
            'avg_hit_rate': strategy.get('aggregate', {}).get('avg_hit_rate', 0.0),
            'alpha_registry_count': alpha.get('counts', {}).get('registry', 0),
            'top_alpha_rank_score': (alpha.get('latest_ranking') or {}).get('rank_score'),
        },
        'strategy': strategy,
        'alpha_factory': alpha,
    }
