from ai_hedge_bot.services.trading_service import TradingService


def test_service_run_once_returns_phaseb_payload():
    service = TradingService()
    result = service.run_once()
    assert 'portfolio_regime' in result
    assert 'alpha_performance' in result
    assert 'regime_performance' in result
    assert 'analytics_sync' in result
