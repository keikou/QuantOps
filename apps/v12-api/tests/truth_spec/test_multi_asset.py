from tests.truth_layer.conftest import MarkSpec, state_value


def test_multi_asset_positions_do_not_bleed_together(
    engine,
    fill_factory,
    apply_fill,
    apply_mark,
    get_state,
):
    apply_fill(engine, fill_factory(fill_id="btc-1", side="buy", qty=1.0, price=100.0, symbol="BTC", ts=1))
    apply_fill(engine, fill_factory(fill_id="eth-1", side="buy", qty=2.0, price=50.0, symbol="ETH", ts=2))

    apply_mark(engine, MarkSpec(symbol="BTC", price=110.0, ts=3))
    apply_mark(engine, MarkSpec(symbol="ETH", price=55.0, ts=3))

    state = get_state(engine)
    total_unrealized = state_value(state, "unrealized_pnl", "unrealized", "pnl_unrealized")
    assert total_unrealized == 20.0
