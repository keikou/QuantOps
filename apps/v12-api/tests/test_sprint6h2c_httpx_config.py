from pathlib import Path
import httpx

from ai_hedge_bot.data.collectors.binance_public_client import BinancePublicClient


class _OkResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {'bidPrice': '100.0', 'askPrice': '101.0'}


class _DummyClient:
    def __init__(self, response=None, error=None, **kwargs):
        self._response = response or _OkResponse()
        self._error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        if self._error is not None:
            raise self._error
        return self._response


def test_fetch_best_bid_ask_uses_httpx_client(monkeypatch):
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: _DummyClient())
    client = BinancePublicClient()
    quote = client.fetch_best_bid_ask('BTCUSDT')
    assert quote.source == 'binance_rest_book_ticker_live'
    assert quote.bid == 100.0
    assert quote.ask == 101.0
    assert quote.stale is False


def test_fetch_best_bid_ask_classifies_httpx_timeout(monkeypatch):
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: _DummyClient(error=httpx.ReadTimeout('boom')))
    client = BinancePublicClient()
    quote = client.fetch_best_bid_ask('BTCUSDT')
    assert quote.source == 'synthetic_quote_fallback'
    assert quote.fallback_reason == 'httpx_timeout'
    assert quote.stale is True


def test_env_examples_are_aligned_for_full_runtime():
    root = Path(__file__).resolve().parents[3]
    env_example = (root / '.env.example').read_text(encoding='utf-8')
    env_full = (root / '.env.full.example').read_text(encoding='utf-8')
    for key in [
        'V12_API_PUBLIC_PORT',
        'QUANTOPS_PUBLIC_PORT',
        'AHB_USE_LIVE_MARKET_DATA',
        'AHB_PRICE_SOURCE',
        'AHB_ALLOW_SYNTHETIC_QUOTE_FALLBACK',
        'AHB_STRICT_LIVE_QUOTES',
        'AHB_BINANCE_REST_BASE_URL',
        'AHB_QUOTE_TIMEOUT_SEC',
    ]:
        assert key in env_example
        assert key in env_full
