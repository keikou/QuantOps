from ai_hedge_bot.scheduler.nightly_weight_update import run
from ai_hedge_bot.services.trading_service import TradingService
from ai_hedge_bot.core.settings import SETTINGS


def test_nightly_scheduler_runs_after_signal_cycle():
    service = TradingService()
    service.run_once()
    result = run()
    assert 'weights' in result
    assert SETTINGS.weights_path.exists()
