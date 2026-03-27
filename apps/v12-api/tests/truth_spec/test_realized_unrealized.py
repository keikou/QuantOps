from tests.truth_layer.conftest import state_value


def test_realized_and_unrealized_are_separated(
    engine,
    fill_factory,
    mark_factory,
    apply_fill,
    apply_mark,
    get_state,
):
    apply_fill(engine, fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1))
    apply_mark(engine, mark_factory(price=110.0, ts=2))

    state_open = get_state(engine)
    assert state_value(state_open, "unrealized_pnl", "unrealized", "pnl_unrealized") == 10.0
    assert state_value(state_open, "realized_pnl", "realized", "pnl_realized") == 0.0

    apply_fill(engine, fill_factory(fill_id="s1", side="sell", qty=1.0, price=110.0, ts=3))
    state_closed = get_state(engine)

    assert state_value(state_closed, "realized_pnl", "realized", "pnl_realized") == 10.0
    assert state_value(state_closed, "unrealized_pnl", "unrealized", "pnl_unrealized") == 0.0
