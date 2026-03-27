from tests.truth_layer.conftest import state_value


def test_latest_mark_source_is_used_consistently(
    engine,
    fill_factory,
    mark_factory,
    apply_fill,
    apply_mark,
    get_state,
):
    apply_fill(engine, fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1))

    apply_mark(engine, mark_factory(price=105.0, ts=2))
    apply_mark(engine, mark_factory(price=110.0, ts=2))
    state = get_state(engine)

    mark = state_value(state, "mark_price", "mark", "last_mark")
    unrealized = state_value(state, "unrealized_pnl", "unrealized", "pnl_unrealized")

    assert mark in {105.0, 110.0}
    assert unrealized == mark - 100.0
