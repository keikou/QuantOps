from ai_hedge_bot.services.trading_service import TradingService


def test_phasea_run_once_returns_extended_payload():
    service = TradingService()
    out = service.run_once()
    assert 'alpha_performance' in out
    assert 'regime_performance' in out
    assert 'portfolio_regime' in out
    assert out['weights_update_applied'] in (True, False)
