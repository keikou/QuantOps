from tests.truth_layer.conftest import state_value


def test_flip_resets_avg(engine, fill_factory, apply_fill, get_state):
    apply_fill(engine, fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1))
    apply_fill(engine, fill_factory(fill_id="s1", side="sell", qty=2.0, price=110.0, ts=2))

    state = get_state(engine)

    assert state_value(state, "position_qty", "qty", "net_qty") == -1.0
    assert state_value(state, "avg_price", "average_price", "avg") == 110.0
    assert state_value(state, "realized_pnl", "realized", "pnl_realized") == 10.0
