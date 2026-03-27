import pytest
from tests.truth_layer.truth_engine_adapter import TruthEngineAdapter as TruthEngine


def test_fill_idempotency():
    engine = TruthEngine()

    fill = {
        "fill_id": "f1",
        "symbol": "BTC",
        "side": "buy",
        "qty": 1.0,
        "price": 100.0,
        "fee": 0.0,
    }

    engine.apply_fill(fill)
    s1 = engine.get_state()

    engine.apply_fill(fill)  # duplicate
    s2 = engine.get_state()

    assert s1["position_qty"] == s2["position_qty"]
    assert s1["avg_price"] == s2["avg_price"]
    assert s1["realized_pnl"] == s2["realized_pnl"]


def test_flip_resets_avg():
    engine = TruthEngine()

    engine.apply_fill({
        "fill_id": "b1", "symbol": "BTC", "side": "buy", "qty": 1, "price": 100
    })
    engine.apply_fill({
        "fill_id": "s1", "symbol": "BTC", "side": "sell", "qty": 2, "price": 110
    })

    s = engine.get_state()

    assert s["position_qty"] == -1
    assert s["avg_price"] == 110
    assert s["realized_pnl"] == 10


def test_realized_unrealized():
    engine = TruthEngine()

    engine.apply_fill({
        "fill_id": "b2", "symbol": "BTC", "side": "buy", "qty": 1, "price": 100
    })

    engine.apply_mark("BTC", 110, ts=1)
    s1 = engine.get_state()

    assert s1["unrealized_pnl"] == 10
    assert s1["realized_pnl"] == 0

    engine.apply_fill({
        "fill_id": "s2", "symbol": "BTC", "side": "sell", "qty": 1, "price": 110
    })

    s2 = engine.get_state()

    assert s2["realized_pnl"] == 10
    assert s2["unrealized_pnl"] == 0


def test_equity_rebuild():
    engine = TruthEngine()

    fills = [
        {"fill_id": "b3", "symbol": "BTC", "side": "buy", "qty": 1, "price": 100},
        {"fill_id": "b4", "symbol": "BTC", "side": "buy", "qty": 1, "price": 120},
    ]

    for f in fills:
        engine.apply_fill(f)

    engine.apply_mark("BTC", 130, ts=1)

    live = engine.get_state()

    rebuilt = engine.rebuild_from_history(fills=fills, marks=[("BTC", 130, 1)])

    assert rebuilt["position_qty"] == live["position_qty"]
    assert rebuilt["avg_price"] == live["avg_price"]
    assert rebuilt["total_equity"] == live["total_equity"]
