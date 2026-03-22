from datetime import datetime, timedelta, timezone

from ai_hedge_bot.core.types import Signal
from ai_hedge_bot.portfolio.portfolio_engine import PortfolioEngine


def make_signal(idx: int, family: str, entry: float):
    return Signal(
        signal_id=f's{idx}',
        symbol='BTCUSDT' if idx < 2 else f'X{idx}',
        timestamp=datetime.now(timezone.utc) + timedelta(minutes=idx),
        side='long',
        entry=entry,
        stop=entry - 1,
        target=entry + 1,
        net_score=0.9,
        confidence=1.0,
        dominant_alpha=f'a{idx}',
        dominant_alpha_family=family,
        signal_horizon='short',
        signal_factor_type='flow',
        signal_signature=f'sig{idx}',
    )


def test_phasea_portfolio_family_cap_and_diagnostics():
    signals = [
        make_signal(0, 'momentum', 100.0),
        make_signal(1, 'momentum', 100.5),
        make_signal(2, 'orderflow', 102.0),
        make_signal(3, 'event', 104.0),
    ]
    engine = PortfolioEngine(max_gross_exposure=1.0, max_symbol_weight=0.35, family_weight_cap=0.50)
    intents, diagnostics = engine.build(signals, regime='trend_up')
    assert diagnostics['selected_count'] >= 2
    assert 'family_concentration' in diagnostics
    assert 'overlap_penalty_summary' in diagnostics
