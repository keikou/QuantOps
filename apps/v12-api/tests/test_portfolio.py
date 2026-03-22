from datetime import datetime, timezone
from ai_hedge_bot.core.types import Signal
from ai_hedge_bot.portfolio.portfolio_engine import PortfolioEngine


def make_signal(i, sig, score):
    return Signal(f's{i}', 'BTCUSDT', datetime.now(timezone.utc), 'long', 100.0, 95.0, 110.0, score, 0.7, 'trend_alpha', 'momentum', 'short', 'trend', sig)


def test_dedup_and_cap():
    engine = PortfolioEngine(max_gross_exposure=0.5, max_symbol_weight=0.35)
    intents, diag = engine.build([make_signal(1, 'dup', 0.4), make_signal(2, 'dup', 0.3)])
    assert len(intents) == 1
    assert diag['dedup_removed_count'] == 1
    assert sum(i.target_weight for i in intents) <= 0.5
