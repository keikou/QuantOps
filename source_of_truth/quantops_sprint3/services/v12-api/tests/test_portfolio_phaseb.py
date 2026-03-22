from datetime import datetime, timezone

from ai_hedge_bot.core.types import Signal
from ai_hedge_bot.portfolio.portfolio_engine import PortfolioEngine
from ai_hedge_bot.portfolio.overlap_manager import OverlapManager


def _signal(sig_id: str, symbol: str, family: str, entry: float, score: float):
    return Signal(sig_id, symbol, datetime.now(timezone.utc), 'long', entry, entry*0.99, entry*1.01, score, 1.0, 'x', family, 'short', 'flow', f'{symbol}|long|{family}|{round(entry,1)}')


def test_overlap_manager_scores_same_symbol():
    manager = OverlapManager()
    base = _signal('a','BTCUSDT','momentum',100,0.5)
    other = _signal('b','BTCUSDT','momentum',101,0.6)
    comps = manager.score_components(other,[base])
    assert comps['symbol_overlap'] > 0


def test_portfolio_engine_returns_diagnostics():
    engine = PortfolioEngine()
    signals = [_signal('a','BTCUSDT','momentum',100,0.6), _signal('b','ETHUSDT','mean_reversion',200,0.5)]
    intents, diagnostics = engine.build(signals, regime='range')
    assert len(intents) >= 1
    assert 'overlap_penalty_summary' in diagnostics
    assert 'family_concentration' in diagnostics
