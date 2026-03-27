from tests.truth_layer.conftest import state_value


def test_same_fill_twice_is_noop(engine, fill_factory, apply_fill, get_state):
    fill = fill_factory(fill_id="f1", side="buy", qty=1.0, price=100.0, ts=1)

    apply_fill(engine, fill)
    state_once = get_state(engine)

    apply_fill(engine, fill)
    state_twice = get_state(engine)

    assert state_value(state_once, "position_qty", "qty", "net_qty") == state_value(
        state_twice, "position_qty", "qty", "net_qty"
    )
    assert state_value(state_once, "avg_price", "average_price", "avg") == state_value(
        state_twice, "avg_price", "average_price", "avg"
    )
    assert state_value(state_once, "realized_pnl", "realized", "pnl_realized") == state_value(
        state_twice, "realized_pnl", "realized", "pnl_realized"
    )
