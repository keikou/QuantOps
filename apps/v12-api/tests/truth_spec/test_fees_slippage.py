from tests.truth_layer.conftest import state_value


def test_fees_reduce_realized_pnl(engine, fill_factory, apply_fill, get_state):
    apply_fill(engine, fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1, fee=0.1))
    apply_fill(engine, fill_factory(fill_id="s1", side="sell", qty=1.0, price=110.0, ts=2, fee=0.1))

    state = get_state(engine)
    realized = state_value(state, "realized_pnl", "realized", "pnl_realized")

    assert realized == 9.8
