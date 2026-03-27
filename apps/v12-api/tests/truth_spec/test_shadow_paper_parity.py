from tests.truth_layer.conftest import state_value


def _engine_with_mode(engine_class, mode: str):
    try:
        return engine_class(mode=mode)
    except TypeError:
        return engine_class()


def test_shadow_and_paper_match_for_same_event_stream(
    engine_class,
    fill_factory,
    mark_factory,
    apply_fill,
    apply_mark,
    get_state,
):
    paper = _engine_with_mode(engine_class, "paper")
    shadow = _engine_with_mode(engine_class, "shadow")

    fills = [
        fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1),
        fill_factory(fill_id="s1", side="sell", qty=1.0, price=110.0, ts=2),
    ]
    marks = [mark_factory(price=105.0, ts=1), mark_factory(price=110.0, ts=2)]

    for engine in (paper, shadow):
        for fill in fills:
            apply_fill(engine, fill)
        for mark in marks:
            apply_mark(engine, mark)

    paper_state = get_state(paper)
    shadow_state = get_state(shadow)

    assert state_value(paper_state, "position_qty", "qty", "net_qty") == state_value(
        shadow_state, "position_qty", "qty", "net_qty"
    )
    assert state_value(paper_state, "realized_pnl", "realized", "pnl_realized") == state_value(
        shadow_state, "realized_pnl", "realized", "pnl_realized"
    )
    assert state_value(paper_state, "total_equity", "equity", "account_equity") == state_value(
        shadow_state, "total_equity", "equity", "account_equity"
    )
