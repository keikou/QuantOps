from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.enums import Mode
from ai_hedge_bot.services.live_trading_service import LiveTradingService


def _reset_phase6_state() -> None:
    for table in ["runtime_control_state", "audit_logs", "runtime_events"]:
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
