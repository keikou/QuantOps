from tests.truth_layer.conftest import state_value


def test_rebuild_matches_live_state(
    engine,
    fill_factory,
    mark_factory,
    apply_fill,
    apply_mark,
    get_state,
    rebuild_from_history,
):
    fills = [
        fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1),
        fill_factory(fill_id="b2", side="buy", qty=1.0, price=120.0, ts=2),
    ]
    for fill in fills:
        apply_fill(engine, fill)

    marks = [mark_factory(price=130.0, ts=3)]
    for mark in marks:
        apply_mark(engine, mark)

    live = get_state(engine)
    rebuilt = rebuild_from_history(engine, fills=fills, marks=marks)

    assert state_value(rebuilt, "position_qty", "qty", "net_qty") == state_value(
        live, "position_qty", "qty", "net_qty"
    )
    assert state_value(rebuilt, "avg_price", "average_price", "avg") == state_value(
        live, "avg_price", "average_price", "avg"
    )
    assert state_value(rebuilt, "total_equity", "equity", "account_equity") == state_value(
        live, "total_equity", "equity", "account_equity"
    )
