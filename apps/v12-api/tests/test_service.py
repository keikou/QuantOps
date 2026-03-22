from ai_hedge_bot.services.trading_service import TradingService


def test_run_once_returns_closed_loop_payload():
    service = TradingService()
    out = service.run_once()
    assert 'signals' in out
    assert 'weights' in out
    assert 'analytics_sync' in out
