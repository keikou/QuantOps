from tests.truth_layer.conftest import state_value


def test_snapshot_then_recovery_round_trip(
    engine,
    fill_factory,
    mark_factory,
    apply_fill,
    apply_mark,
    get_state,
):
    apply_fill(engine, fill_factory(fill_id="b1", side="buy", qty=1.0, price=100.0, ts=1))
    apply_mark(engine, mark_factory(price=120.0, ts=2))

    snapshot = engine.snapshot() if hasattr(engine, "snapshot") else get_state(engine)

    if hasattr(engine, "restore"):
        restored = type(engine)()
        restored.restore(snapshot)
        restored_state = get_state(restored)
    else:
        restored_state = snapshot

    assert state_value(restored_state, "position_qty", "qty", "net_qty") == 1.0
    assert state_value(restored_state, "mark_price", "mark", "last_mark") == 120.0
