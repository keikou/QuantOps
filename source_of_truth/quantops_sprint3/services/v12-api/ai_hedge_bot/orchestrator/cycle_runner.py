from __future__ import annotations

from ai_hedge_bot.orchestrator.backtest_orchestrator import BacktestOrchestrator
from ai_hedge_bot.orchestrator.paper_orchestrator import PaperOrchestrator
from ai_hedge_bot.orchestrator.shadow_orchestrator import ShadowOrchestrator
from ai_hedge_bot.orchestrator.live_orchestrator import LiveOrchestrator


def run_mode_cycle(mode: str) -> dict:
    orchestrators = {
        'backtest': BacktestOrchestrator(),
        'paper': PaperOrchestrator(),
        'shadow': ShadowOrchestrator(),
        'live': LiveOrchestrator(),
    }
    return orchestrators[mode].run_cycle()
