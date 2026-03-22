from fastapi.testclient import TestClient

from ai_hedge_bot.app.main import app
from ai_hedge_bot.execution.paper_executor import PaperExecutor
from ai_hedge_bot.core.types import PortfolioIntent

client = TestClient(app)


def test_market_quote_config_endpoint_exposes_runtime_source_settings() -> None:
    response = client.get('/market/quote-config')
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'price_source' in payload['config']
    assert 'binance_rest_base_url' in payload['config']


def test_paper_executor_accepts_quote_metadata_dicts() -> None:
    executor = PaperExecutor()
    intent = PortfolioIntent(symbol='BTCUSDT', side='long', target_weight=0.25, signal_id='sig1', net_score=1.0)
    fills = executor.execute([intent], {'BTCUSDT': {'mark_price': 70123.45, 'source': 'binance_rest_book_ticker_live'}})
    assert fills[0].fill_price == 70123.45
    positions = executor.mark_to_market({'BTCUSDT': {'mark_price': 70200.0}})
    assert positions[0].mark_price == 70200.0
