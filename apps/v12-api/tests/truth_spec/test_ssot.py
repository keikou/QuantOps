from tests.truth_layer.conftest import state_value


def test_position_and_portfolio_views_are_consistent(
    engine,
    fill_factory,
    mark_factory,
    apply_fill,
    apply_mark,
    get_state,
):
    apply_fill(engine, fill_factory(fill_id="b1", side="buy", qty=2.0, price=100.0, ts=1))
    apply_mark(engine, mark_factory(price=110.0, ts=2))

    state = get_state(engine)

    qty = state_value(state, "position_qty", "qty", "net_qty")
    exposure = state_value(state, "gross_exposure", "position_notional", "exposure")

    assert qty == 2.0
    assert exposure == qty * 110.0
