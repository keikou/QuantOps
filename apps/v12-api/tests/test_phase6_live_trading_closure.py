from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.enums import Mode
from ai_hedge_bot.services.live_trading_service import LiveTradingService


def _reset_phase6_state() -> None:
    for table in [
        "runtime_control_state",
        "audit_logs",
        "runtime_events",
        "live_orders",
        "live_fills",
        "live_account_balances",
        "live_reconciliation_events",
        "live_incidents",
    ]:
        try:
            CONTAINER.runtime_store.execute(f"DELETE FROM {table}")
        except Exception:
            pass


def test_phase6_close1_approved_live_intent_yields_explicit_send_or_block_decision() -> None:
    _reset_phase6_state()
    service = LiveTradingService()
    service.runtime_service.resume_trading("phase6 reset", actor="test")

    blocked = service.evaluate_live_intent(
        symbol="BTCUSDT",
        urgency="high",
        target_weight=0.30,
        approved=True,
        mode=Mode.PAPER,
    )
    assert blocked["status"] == "blocked"
    assert blocked["decision"] == "live_block"
    assert blocked["reason_code"] == "live_mode_disabled"

    first_send = service.evaluate_live_intent(
        symbol="BTCUSDT",
        urgency="high",
        target_weight=0.30,
        approved=True,
        mode=Mode.LIVE,
    )
    second_send = service.evaluate_live_intent(
        symbol="BTCUSDT",
        urgency="high",
        target_weight=0.30,
        approved=True,
        mode=Mode.LIVE,
    )

    assert first_send["status"] == "ok"
    assert first_send["decision"] == "live_send"
    assert first_send["reason_code"] is None
    assert first_send["route"]["venue"] == "binance_live"
    assert first_send["route"]["order_type"] == "market"
    assert first_send["route"]["tif"] == "IOC"
    assert first_send == second_send


def test_phase6_close1_halted_runtime_blocks_even_approved_live_intent() -> None:
    _reset_phase6_state()
    service = LiveTradingService()
    service.runtime_service.halt_trading("phase6 halt", actor="test")

    blocked = service.evaluate_live_intent(
        symbol="ETHUSDT",
        urgency="high",
        target_weight=0.25,
        approved=True,
        mode=Mode.LIVE,
    )

    assert blocked["status"] == "blocked"
    assert blocked["decision"] == "live_block"
    assert blocked["reason_code"] == "execution_disabled"
    assert blocked["trading_state"] == "halted"


def test_phase6_close2_live_send_persists_lifecycle_and_reconciliation_evidence() -> None:
    _reset_phase6_state()
    service = LiveTradingService()
    service.runtime_service.resume_trading("phase6 close2 reset", actor="test")

    submitted = service.submit_live_order(
        symbol="BTCUSDT",
        side="buy",
        qty=0.25,
        urgency="high",
        target_weight=0.30,
        approved=True,
        mode=Mode.LIVE,
    )
    assert submitted["status"] == "ok"
    assert submitted["decision"] == "live_send"
    assert submitted["order_status"] == "submitted"

    submitted_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT status, venue, order_type, tif, venue_order_id FROM live_orders WHERE live_order_id = ?",
        [submitted["live_order_id"]],
    )
    assert submitted_row is not None
    assert submitted_row["status"] == "submitted"
    assert submitted_row["venue"] == "binance_live"
    assert submitted_row["order_type"] == "market"
    assert submitted_row["tif"] == "IOC"
    assert submitted_row["venue_order_id"] == submitted["venue_order_id"]

    reconcile = service.reconcile_live_fill(
        live_order_id=submitted["live_order_id"],
        venue_order_id=submitted["venue_order_id"],
        symbol="BTCUSDT",
        side="buy",
        fill_qty=0.25,
        fill_price=100000.0,
        free_balance=9500.0,
        locked_balance=500.0,
        matched=True,
    )
    assert reconcile["status"] == "ok"
    assert reconcile["order_status"] == "filled"
    assert reconcile["matched"] is True

    filled_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT status FROM live_orders WHERE live_order_id = ?",
        [submitted["live_order_id"]],
    )
    assert filled_row is not None
    assert filled_row["status"] == "filled"

    fill_count = CONTAINER.runtime_store.fetchone_dict(
        "SELECT COUNT(*) AS c FROM live_fills WHERE live_order_id = ?",
        [submitted["live_order_id"]],
    )
    assert int(fill_count["c"]) == 1

    balance_row = CONTAINER.runtime_store.fetchone_dict(
        "SELECT asset, total_balance, source FROM live_account_balances ORDER BY created_at DESC LIMIT 1"
    )
    assert balance_row is not None
    assert balance_row["asset"] == "USDT"
    assert float(balance_row["total_balance"]) == 10000.0
    assert balance_row["source"] == "reconciliation"

    events = CONTAINER.runtime_store.fetchall_dict(
        """
        SELECT event_type, status, matched
        FROM live_reconciliation_events
        WHERE live_order_id = ?
        ORDER BY created_at ASC
        """,
        [submitted["live_order_id"]],
    )
    assert [row["event_type"] for row in events] == ["order_submitted", "fill_reconciled"]
    assert events[-1]["status"] == "ok"
    assert bool(events[-1]["matched"]) is True

    incident_count = CONTAINER.runtime_store.fetchone_dict("SELECT COUNT(*) AS c FROM live_incidents")
    assert int(incident_count["c"]) == 0
